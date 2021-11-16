from f3dasm.simulator.fenics_wrapper.model.domain import Domain
from f3dasm.simulator.fenics_wrapper.model.materials.neohookean import NeoHookean
from f3dasm.simulator.fenics_wrapper.model.materials.svenan_kirchhoff import SVenantKirchhoff
from f3dasm.simulator.fenics_wrapper.problems.problem_base import ProblemBase 

from dolfin import *
import numpy as np
import copy as cp


class RVE(ProblemBase):
    """ 
        General RVE model implementation
    """
    def __init__(self, options, domain_filename, F_macro, name=None):
        domain = Domain(domain_filename)
        super().__init__(options=options, name=name, domain=domain)

        ################################
        # Define function spaces for the problem
        ################################
        self.Ve = VectorElement("CG", self.domain.mesh.ufl_cell(), 1)

        ################################
        # Define function space for the pure Neumann Lagrange multiplier
        ################################
        self.Re = VectorElement("R", self.domain.mesh.ufl_cell(), 0)

        self.bc_p = PeriodicBoundary(self.domain,periodicity=[0,1],tolerance=1e-10)   # Initialize periodic boundary conditions

        ################################
        # Mixed function space initialization with periodic boundary conditions
        ################################
        self.W = FunctionSpace(self.domain.mesh, MixedElement([self.Ve, self.Re]), constrained_domain=self.bc_p)

        self.F_macro = F_macro
        self.convergence = True


        # Define the variational problem for with pure neumann boundary condition

        v_,lamb_ = TestFunctions(self.W)                # Define test functions 
        dv, dlamb = TrialFunctions(self.W)              # Define trial functions 
        self.w = Function(self.W)
        
        ################################
        # F_macro should be defined locally because when passing in another way
        # it gives erroneous results! So for consistancy it is defined just before
        # passing as Constant from fenics.
        ################################
        F_macro = Constant(self.F_macro)                

        u,c = split(self.w)

        ################################
        # Define materials for phases
        ################################
        self.material = [NeoHookean(u,F_macro, E=300, nu=0.1),SVenantKirchhoff(u,F_macro,E=500,nu=0.3)]        # model-1

        
        dx = Measure('dx')(subdomain_data=self.domain.subdomains)       # Redefine dx for subdomains

        ################################
        # Variational problem definition -> Lagrangian Linear Momentum Equation
        ################################
        self.PI = inner(self.material[0].P,nabla_grad(v_))*dx(1) + inner(self.material[1].P,nabla_grad(v_))*dx(2)  

        self.PI += dot(lamb_,u)*dx + dot(c,v_)*dx


    def solve(self):

        """ Method: Define solver options with your solver """

        prm = {"newton_solver":
                {"absolute_tolerance":1e-7,'relative_tolerance':1e-7,'relaxation_parameter':1.0}}
        try:
            solve(self.PI==0, self.w, [],solver_parameters=prm,form_compiler_parameters={"optimize": True})
            (self.v, lamb) = self.w.split(True)
        except:
            self.convergence = False
       # self.__deformed()


    def postprocess(self):
        """ 
            Method: postprocess implementation to get the homogenized 
                    second Piola-Kirchhoff stress tensor 
        """
        if self.convergence is False:
            S = np.zeros((self.domain.dim,self.domain.dim))
        else:
            
            P = self.__project_P()                          # Project first Piola-Kirchhoff stress tensor 
            filename = File('stress.pvd')
            filename << P
            F = self.__project_F()                          # Project Deformation Gradient

            Piola = P.split(True)
            DG = F.split(True)
            P_hom = np.zeros(self.domain.dim**2) 
            F_hom = np.zeros(self.domain.dim**2) 
            
            for i in range(self.domain.dim**2):
                for j in range(self.domain.ele_num):
                    P_hom[i] = np.dot(Piola[i].vector().get_local(),self.domain.ele_vol)/self.domain.vol

                    F_hom[i] = (DG[i].vector().get_local().mean())

            P_hom = P_hom.reshape(-1,self.domain.dim)
            F_hom = F_hom.reshape(-1,self.domain.dim)
            S = np.dot(np.linalg.inv(F_hom.T),P_hom)


        
        return S, F_hom

    def __deformed(self):

        """ Method: output the deformed state to a file """

        V = FunctionSpace(self.domain.mesh,self.Ve)
        y = SpatialCoordinate(self.domain.mesh)
        write = dot(Constant(self.F_macro),y)+self.v
        filename = File("deformation.pvd")
        filename << project(write,V)

        ################################
        # Easy ploting for the 2D deformation
        ################################
        #y = SpatialCoordinate(self.domain.mesh)
        ##F = Identity(self.domain.dim) + grad(self.v) + Constant(self.F_macro)              # Deformation gradient
        #p = plot(dot(Constant(self.F_macro),y)+self.v, mode="displacement")
        ##p = plot(self.v, mode="displacement")
        ##p = plot(self.stress[0, 0])
        #plt.colorbar(p)
        #plt.savefig("rve_deformed.pdf")

    def __project_P(self):

        """ 
            Method: Projecting first Piola-Kirchhoff stress tensor.
                    Another linear variational problem has to be solved.
        """

        V = TensorFunctionSpace(self.domain.mesh, "DG",0)           # Define Discontinuous Galerkin space

        ################################
        # Similar type of problem definition inside the model
        ################################
        dx = Measure('dx')(subdomain_data=self.domain.subdomains)   
        dx = dx(metadata={'quadrature_degree': 1})
        dv = TrialFunction(V)
        v_ = TestFunction(V)
        a_proj = inner(dv,v_)*dx
        b_proj = inner(self.material[0].P,v_)*dx(1) +inner(self.material[1].P,v_)*dx(2)
        P = Function(V)
        solve(a_proj==b_proj,P)
        return P

    def __project_F(self):

        """ 
            Method: Projecting deformation gradient.
                    Another linear variational problem has to be solved.
        """

        ################################
        # Similar type of problem definition inside the model
        ################################
        V = TensorFunctionSpace(self.domain.mesh, "DG",0)       # Define Discontinuous Galerkin space

        dx = Measure('dx')(subdomain_data=self.domain.subdomains)
        dv = TrialFunction(V)
        v_ = TestFunction(V)
        a_proj = inner(dv,v_)*dx
        b_proj = inner(self.material[0].F,v_)*dx(1) +inner(self.material[1].F,v_)*dx(2)
        F = Function(V)
        solve(a_proj==b_proj,F)
        return F


class PeriodicBoundary(SubDomain):
    """
        GENERAL PERIODIC BOUNDARY CONDITIONS IMPLEMENTATION

                              #-----------# 
                             / |        / |
                            /  |       /  |
                           #----------#   |
                           *   |      |   |
                           *   #----------# 
                     [1]   *  *       |  / 
                           * * [2]    | / 
                           **         |/  
                           ***********# 
                               [0]

            *   : Master edges/nodes
            -   : Slave edges/nodes 
            [i] : directions for periodicity

   """

    def __init__(self,domain,periodicity=None,tolerance=DOLFIN_EPS):

        """ Initialize """

        super().__init__()              # Initialize the base-class (Note: the tolerance is needed for the mapping method)

        ################################
        # Get the extrema of the domain for every direction
        ################################
        self.mins = np.array(domain.bounds[0])          
        self.maxs = np.array(domain.bounds[1])

        self.directions = np.flatnonzero(self.maxs - self.mins)     # Mark non-zero directions
        
        ################################
        # Definie periodic directions
        ################################
        if periodicity is None:
            self.periodic_dir = self.directions                 

        else:
            self.periodic_dir = periodicity

        self.tol = tolerance 
        self.master = []                                # Master nodes 
        self.map_master = []                            # Mapped master nodes
        self.map_slave = []                             # Mapped slave nodes

    def inside(self,x,on_boundary):
        ################################
        # Mark the master nodes as True 
        ################################
        x_master=False                                                   
        if on_boundary:                                                         
            for axis in self.periodic_dir:                                      
                if near(x[axis],self.maxs[axis],self.tol):
                    x_master=False                                       
                    break
                elif near(x[axis],self.mins[axis],self.tol):
                    x_master=True                                        

        if x_master:
            self.master.append(cp.deepcopy(x))

        return x_master

    # Overwrite map method of SubDomain class to define the mapping master -> slave
    def map(self,x,y):
        ################################
        # Map the master nodes to slaves
        ################################
        x_slave=False                                       
        for axis in self.directions:                               
            if axis in self.periodic_dir:                          
                if near(x[axis],self.maxs[axis],self.tol):
                    y[axis]=self.mins[axis]                        
                    x_slave=True                            
                else:                                              
                    y[axis]=x[axis]                                
            else:                                                  
                y[axis]=x[axis]                                    

        if x_slave:
            self.map_master.append(cp.deepcopy(y))                            # add y to list mapped master coordinates
            self.map_slave.append(cp.deepcopy(x))                             # add x to list of mapped slave coordinates