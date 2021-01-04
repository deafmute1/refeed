from pathlib import Path

config_path = str(Path(__file__).parent.joinpath('config', 'config.yaml')) # cast to str to prevent any mutability. 
log_path = str(Path(__file__).parent.joinpath('log', 'root.log'))
data_path = str(Path(__file__).parent.joinpath('data'))
static_path = str(Path(__file__).parent.joinpath('static'))