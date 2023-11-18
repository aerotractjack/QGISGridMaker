import os
from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsVectorLayer,
    QgsUnitTypes,
    QgsCoordinateReferenceSystem
)
from qgis.analysis import QgsNativeAlgorithms
import sys
sys.path.append("/usr/share/qgis/python/plugins")
import processing
from processing.core.Processing import Processing
from . import integration

QgsApplication.setPrefixPath("/usr/bin/qgis", True)
qgs = QgsApplication([], False)
qgs.initQgis()
Processing.initialize()
qgs.processingRegistry().addProvider(QgsNativeAlgorithms())

def log(msg):
    print(msg)
    sys.stdout.flush()

class GridMaker:

    def __init__(self, shp_path, grid_path, plot_paths):
        self.shp_path = shp_path
        self.grid_path = grid_path
        self.plot_paths = plot_paths
        self.project = QgsProject.instance()
        self.project.setDistanceUnits(QgsUnitTypes.DistanceFeet)
        self.project.setAreaUnits(QgsUnitTypes.AreaAcres)

    def run(self):
        extent_str = self.load_shp()
        self.create_raw_grid(extent_str)
        self.clip_raw_grid()
        self.buffer_clipped_grid()
        return self.plot_paths

    def load_shp(self):
        shp_vlayer = QgsVectorLayer(self.shp_path, "shp", "ogr")
        if not shp_vlayer.isValid():
            raise ValueError(f"INVALID SHP LAYER: {self.shp_path}")
        self.project.setCrs(shp_vlayer.crs())
        self.project.setDistanceUnits(QgsUnitTypes.DistanceFeet)
        self.project.setAreaUnits(QgsUnitTypes.AreaAcres)
        self.project.addMapLayer(shp_vlayer)
        extent = shp_vlayer.extent()
        shp_crs_str = f"[{shp_vlayer.crs().authid()}]"
        extent_str = f"{extent.xMinimum()},{extent.xMaximum()},{extent.yMinimum()},{extent.yMaximum()} {shp_crs_str}"
        return extent_str

    def create_raw_grid(self, extent_str):
        # Define parameters for creating grid
        params = {
            'TYPE': 0, 
            'EXTENT': extent_str,  
            'CRS': 'EPSG:26910',  
            'HSPACING': 500*.308,  
            'VSPACING': 500*.308,  
            'HOVERLAY': 0,
            'VOVERLAY': 0,
            'OUTPUT': self.plot_paths['raw_tpa_plots']
        }
        processing.run("qgis:creategrid", params)

    def clip_raw_grid(self):
        params = {
            'INPUT': self.plot_paths['raw_tpa_plots'],  
            'OVERLAY': self.shp_path,  
            'OUTPUT': self.plot_paths['clipped_tpa_plots']  
        }
        processing.run("qgis:clip", params)

    def buffer_clipped_grid(self):
        params = {
            'INPUT': self.plot_paths['clipped_tpa_plots'],  
            'DISTANCE': 13.7*.308,  
            'SEGMENTS': 5,  
            'END_CAP_STYLE': 0,  
            'JOIN_STYLE': 0,  
            'MITER_LIMIT': 2,  
            'DISSOLVE': False,  
            'OUTPUT': self.plot_paths['buffered_tpa_plots'] 
        }
        processing.run("qgis:buffer", params)

    @classmethod
    def FromIDs(cls, client_id, project_id, stand_id):
        shp_path = integration.get_shp_path(client_id, project_id, stand_id)
        grid_path = integration.get_grid_path(client_id, project_id, stand_id)
        plot_paths = integration.get_plot_paths(client_id, project_id, stand_id)
        return cls(shp_path, grid_path, plot_paths).run()

def FromIDs(client_id, project_id, stand_id):
    return GridMaker.FromIDs(client_id, project_id, stand_id)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", "-c", required=True, help="Client ID")
    parser.add_argument("--project", "-p", required=True, help="Project ID")
    parser.add_argument("--stand", "-s", required=True, help="Stand 3-Digit ID", nargs="+")
    args = parser.parse_args()

    for stand in args.stand:
        msg = f"""
        Starting {args.client}, {args.project}, {stand} 
        """
        log(msg)
        GridMaker.FromIDs(args.client, args.project, stand)

    qgs.exitQgis()

