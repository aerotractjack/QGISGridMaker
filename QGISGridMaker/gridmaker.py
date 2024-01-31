import os
import math
import sys
import traceback
import geopandas as gpd
from qgis.core import (
    QgsApplication,
    QgsProject,
    QgsVectorLayer,
    QgsUnitTypes,
    QgsCoordinateReferenceSystem
)
import processing
from processing.core.Processing import Processing
from qgis.analysis import QgsNativeAlgorithms

from . import integration

from aerologger import AeroLogger
sdk_logger = AeroLogger(
    'QGIS Grid Maker SDK',
    'PlotGridSDK/PlotGridSDK.log'
)
from requires_nas import requires_nas_loop
requires_nas_loop(info_logger=sdk_logger.info, error_logger=sdk_logger.error)

# QGIS Context Manager
class QGISContext:

    def __init__(self):
        self.qgis = None

    def __enter__(self):
        QgsApplication.setPrefixPath("/usr/bin/qgis", True)
        qgs = QgsApplication([], False)
        qgs.initQgis()
        Processing.initialize()
        qgs.processingRegistry().addProvider(QgsNativeAlgorithms())
        self.qgis = qgs
        return self  

    def __exit__(self, exc_type, exc_value, traceback):
        self.qgis.exitQgis()

# QGIS Processing Steps
class GridMaker:

    def __init__(self, shp_path, grid_path, plot_paths):
        self.shp_path = shp_path
        self.grid_path = grid_path # NEVER USED
        self.plot_paths = plot_paths
        self.project = QgsProject.instance()
        self.project.setDistanceUnits(QgsUnitTypes.DistanceFeet)
        self.project.setAreaUnits(QgsUnitTypes.AreaAcres)
        self.shp_crs = None

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
        self.shp_crs = shp_vlayer.crs()
        return extent_str

    def create_raw_grid(self, extent_str):
        grid_ft = 13.7*2
        params = {
            'TYPE': 0, 
            'EXTENT': extent_str,  
            'CRS': 'EPSG:26910',  
            'HSPACING': grid_ft*.308,  
            'VSPACING': grid_ft*.308,  
            'HOVERLAY': 0,
            'VOVERLAY': 0,
            'OUTPUT': self.plot_paths['raw_tpa_plots'],
        }
        processing.run("qgis:creategrid", params)

    def clip_raw_grid(self):
        params = {
            'INPUT': self.plot_paths['raw_tpa_plots'],  
            'OVERLAY': self.shp_path,  
            'OUTPUT': self.plot_paths['clipped_tpa_plots'] ,
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
            'OUTPUT': self.plot_paths['buffered_tpa_plots'],
        }
        processing.run("qgis:buffer", params)

    def calculate_coverage(self, area_acre):
        min_acre = 10
        max_acre = 225
        min_cov = 15
        max_cov = 30
        cov = min_cov + (max_cov - min_cov) * ((area_acre - min_acre) / (max_acre - min_acre))
        return cov

    def post_process_plots(self):
        plots = gpd.read_file(self.plot_paths['buffered_tpa_plots'])
        single_plot_area = math.pi*(13.7**2)
        shp = gpd.read_file(self.shp_path).to_crs("EPSG:32610") 
        area_sq_meter = shp.geometry.area.sum()
        area_acre = area_sq_meter * 0.000247105
        area_sqft = area_sq_meter * 10.7639
        # cov = self.calculate_coverage(area_acre)
        # cov_area = area_sqft * cov
        # n_plots = int(cov_area // single_plot_area)
        n_plots = int(self.calculate_coverage(area_acre))
        plots = plots.sample(n=n_plots)
        plots.to_file(self.plot_paths['buffered_tpa_plots'], crs=plots.crs, driver="GeoJSON")

    def run(self):
        extent_str = self.load_shp()
        self.create_raw_grid(extent_str)
        self.clip_raw_grid()
        self.buffer_clipped_grid()
        self.post_process_plots()
        # os.remove(self.plot_paths['raw_tpa_plots'])
        # os.remove(self.plot_paths['clipped_tpa_plots'])
        return self.plot_paths['buffered_tpa_plots']

    @classmethod
    def FromIDs(cls, client_id, project_id, stand_id):
        sdk_logger.info(f"Generating val plots for {client_id}, {project_id}, {stand_id}")
        try:
            shp_path = integration.get_shp_path(client_id, project_id, stand_id)
            grid_path = integration.get_grid_path(client_id, project_id, stand_id)
            plot_paths = integration.get_plot_paths(client_id, project_id, stand_id)
        except Exception as e:
            sdk_logger.error("Error fetching paths:")
            sdk_logger.error(str(e))
        try:
            plot_path = cls(shp_path, grid_path, plot_paths).run()
            sdk_logger.info(f"Saving paths to {str(plot_path)}")
            return plot_path
        except Exception:
            sdk_logger.error(str(traceback.format_exc()))

def GridMakerFactory(client_id, project_id, stand_id, msg=False, context=True):
    if not isinstance(stand_id, list):
        stand_id = [stand_id]
    def factory(stand_id):
        out = []
        for stand in stand_id:
            if msg:
                print(f"Starting {client_id}, {project_id}, {stand}")
            try:
                plot_path = GridMaker.FromIDs(client_id, project_id, stand)
                out.append(plot_path)
            except Exception as e:
                sdk_logger.error(str(e))
        return out
    if not context:
        return factory(stand_id)
    with QGISContext() as qgc:
        return factory(stand_id)
