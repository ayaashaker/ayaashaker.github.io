""" 
This Class Calculates Properties of a Given Discrete Geometry Tri-Mesh 
This file is intended to run in Rhino due to dependencies
"""
from scriptcontext import sticky
import Rhino.Geometry as rg
import ghpythonlib.treehelpers as th
import math


class Util():
    def sort_by_indices(self, lst, indexes, reverse=False):
      return [val for (_, val) in sorted(zip(indexes, lst), key=lambda x: x[0], reverse=reverse)]
    def remap(self, x, in_min, in_max, out_min, out_max):
      return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
    def remapRangetofixedvalues (self, valueToMap , fixedValuesCount):
      remapedValue = round((fixedValuesCount - 1) * valueToMap)
      return remapedValue
class DiscreteGeo():
    def __init__(self, m):
        self.rgmesh = m
        self.nthPercentile = 10
        self.faces = m.Faces
        self.vertices = m.Vertices
        #compute face Normals
        m.FaceNormals.ComputeFaceNormals()
        m.FaceNormals.UnitizeFaceNormals()
        # collect face normals values
        self.fNormals = [rg.Vector3d(n) for n in m.FaceNormals]
        self.facePlane,_,_,_ = self.getFaceBoundariesAttr()
        _,self.faceB,_,_ = self.getFaceBoundariesAttr()
        _,_,self.faceAreas,_ = self.getFaceBoundariesAttr()
        _,_,_,self.faceCentroids = self.getFaceBoundariesAttr()
        self.averageFaceArea = self.getAvgFaceArea(self.faceAreas, self.faces)
        # collect face idicies based on dir
        self.bottomFaceIndices,_,_ = self.remapNormals()
        _,self.lateralFaceIndices,_ = self.remapNormals()
        _,_,self.topFaceIndices = self.remapNormals()
    def getFaceBoundariesAttr(self):
        """ This Function returns a list of all mesh faces boundaries as Polyline Curve """
        FacePlaneList = []
        FaceBoundariesList = []
        FaceAreasList = []
        FaceCentroidsList = []
        for f in self.faces:
            # Convert vertices to 3dpoints to construct plane, face boundary 
            p1 = rg.Point3d(self.vertices[f.A])
            p2 = rg.Point3d(self.vertices[f.B])
            p3 = rg.Point3d(self.vertices[f.C])
            plane = rg.Plane(p1,p2,p3)
            FacePlaneList.append(plane)
            faceBoundary = rg.PolylineCurve([p1,p2,p3,p1])
            FaceBoundariesList.append(faceBoundary)
            amInfo = rg.AreaMassProperties.Compute(faceBoundary)
            FaceAreasList.append(amInfo.Area)
            FaceCentroidsList.append(amInfo.Centroid)
        return FacePlaneList, FaceBoundariesList, FaceAreasList, FaceCentroidsList
    def getAvgFaceArea(self, FaceAreaList, FacesList):
        """this function return the float value of average face area in a mesh"""
        avgArea = sum(FaceAreaList) / len(FacesList)
        return avgArea
    def getStableConfigurations(self, n = None):
        """ This method directly deploys the getNthPercentFaceData function with default values
        and returns list of transformed meshes and list of the transformation matrix value"""
        trnsMeshList = []
        trnsList = []
        if n is None:
            n = self.nthPercentile
        _, mesh_FaceAreaList, _, mesh_FacePlaneList, mesh_FaceBoundryList = self.getNthPercentFaceData(n)
        for i, p in enumerate(mesh_FacePlaneList):
            p.Flip()
            trns = rg.Transform.PlaneToPlane(p, rg.Plane.WorldXY)
            temp = self.rgmesh.Duplicate()
            temp.Transform(trns)
            temp_amInfo = rg.AreaMassProperties.Compute(temp)
            temp_Cntr = temp_amInfo.Centroid
            projCntr = rg.Point3d(temp_Cntr.X, temp_Cntr.Y,0)
            transformedBoundary = mesh_FaceBoundryList[i].Duplicate()
            transformedBoundary.Transform(trns)
            inclusion_bool = transformedBoundary.Contains(projCntr)
            if int(inclusion_bool) == 1:
                trnsMeshList.append(temp)
                trnsList.append((p, rg.Plane.WorldXY)) #break
            else:
                continue
        return trnsMeshList, trnsList
class DiscreteGeoOperations():
    def findFacePairs(self, FixedMesh, MeshToOrient, pairingMode, tolerance = 0.05):
        """ pairingMode: 
        0 = vertical    
        1 = lateral """
        #Step 1: Collect list of faces to pair
        fixedMeshFacesId = []
        MeshToOrientFacesId = []
        if pairingMode == 0:
            fixedMeshFacesId = FixedMesh.topFaceIndices
            MeshToOrientFacesId = MeshToOrient.bottomFaceIndices
        elif pairingMode == 1:
            fixedMeshFacesId = FixedMesh.lateralFaceIndices
            MeshToOrientFacesId = MeshToOrient.lateralFaceIndices
        fixedMeshVectors = [FixedMesh.fNormals[i] for i in fixedMeshFacesId]
        FixedMeshCenters = [FixedMesh.faceCentroids[i] for i in fixedMeshFacesId]
        MeshToOrientFacesVectors = [MeshToOrient.fNormals[i] for i in MeshToOrientFacesId]
        MeshToOrientCenters = [MeshToOrient.faceCentroids[i] for i in MeshToOrientFacesId]  
        #Step 2: check list length to determine looping heirarchy
        """ returns tuples (fixedMeshFace, MeshToOrient) """
        facePairs= []
        if len(fixedMeshVectors) < len(MeshToOrientFacesVectors):
            for ia, fA in enumerate(fixedMeshVectors):
                for ib, fB in enumerate(MeshToOrientFacesVectors):
                    vAngle = rg.Vector3d.VectorAngle(fA,fB)
                    #if Faces are parallel (within given tolerance)
                    if ( (math.pi-tolerance) <= vAngle <= (math.pi+tolerance)):
                        facePairs.append((ia,ib))
        elif len(fixedMeshVectors) >= len(MeshToOrientFacesVectors):
            for ia, fA in enumerate(MeshToOrientFacesVectors):
                for ib, fB in enumerate(fixedMeshVectors):
                    vAngle = rg.Vector3d.VectorAngle(fA,fB)
                    #if Faces are parallel (within given tolerance)
                    if ((math.pi-tolerance) <= vAngle <= (math.pi+tolerance)):
                        facePairs.append((ib,ia))
        return facePairs, fixedMeshVectors, MeshToOrientFacesVectors, FixedMeshCenters, MeshToOrientCenters

#Share Class
sticky["DiscreteGeoClass"] = DiscreteGeo
sticky["DiscreteGeoOperationsClass"] = DiscreteGeoOperations