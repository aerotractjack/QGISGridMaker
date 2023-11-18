import requests
from pathlib import Path

storage_api_url = "http://192.168.1.35:7111"

def get_shp_path(client_id, project_id, stand_id):
    body = {
        "entry": {
            "CLIENT_ID": client_id,
            "PROJECT_ID": project_id,
            "STAND_ID": stand_id
        },
        "filetype": "site_shapefile"
    }
    url = storage_api_url + "/filepath"
    req = requests.post(url, json=body)
    if not req.status_code == 200:
        raise ValueError("API call failed: " + str(req.text))
    return req.json()['filepath']

def get_plot_paths(client_id, project_id, stand_id):
    fts = ['raw_tpa_plots', 'clipped_tpa_plots', 'buffered_tpa_plots']
    out = {}
    for ft in fts:
        body = {
            "entry": {
                "CLIENT_ID": client_id,
                "PROJECT_ID": project_id,
                "STAND_ID": stand_id
            },
            "filetype": ft
        }
        url = storage_api_url + "/filepath"
        req = requests.post(url, json=body)
        if not req.status_code == 200:
            raise ValueError("API call failed: " + str(req.text))
        fp = req.json()['filepath']
        Path(fp).parent.mkdir(exist_ok=True, parents=True)
        out[ft] = fp
    return out

def get_grid_path(client_id, project_id, stand_id):
    return "/home/aerotract/NAS/main/Clients/10007_Chinook/101031_Chinook_WA_Chelan_2023/example_100_grid.geojson"
    # body = {
    #     "entry": {
    #         "CLIENT_ID": client_id,
    #         "PROJECT_ID": project_id,
    #         "STAND_ID": stand_id
    #     },
    #     "filetype": "site_shapefile"
    # }
    # url = storage_api_url + "/filepath"
    # req = requests.post(url, json=body)
    # if not req.status_code == 200:
    #     raise ValueError("API call failed: " + str(req.text))
    # return req.json()['filepath']

if __name__ == "__main__":
    print(get_plot_paths(10007, 101031, 100))