**UNDER CONSTRUCTION**

# REFEED 

# Install 
## Bare
1. Install required distro packages (note that on some very minimal install, more than this may be required; also that some packages may have different names on your distro.)
    
    `python3-pip` 

    The minimum installed python verison is at least 3.7, although 3.8 or 3.9 are more likely to be compatible. 

2. Get the latest release and install it to a location of your choice (e.g. /opt): 
    
    `cd /opt && wget <Link to release tarball> -O - | tar -xz -C /opt/refeed `

    Or install from git master:
    
    `cd /opt && sudo git clone https://github.com/deafmute1/refeed.git`

3. Install required pip packages (preferrably into a virtual env, if you are an end user consider using `pipx`): 
    `cd /opt/refeed && pip3 install -r min_requirements.txt`
   
    For devs, use `dev_requirements.txt`. 

4. Setup your refeed config in a location of your choice (default is (from git root) /run/config.yaml), and run refeed: 
     `python3 /opt/refeed/refeed.py <path to config.yaml>  & `
    
    You may want to setup a systemd service file or find some other way to autostart refeed.
    
    See [below](https://github.com/deafmute1/docker-calibredb#config.yaml) to setup your config file. 
  
5. Point a web server to whatever you have set the static directory as (default <refeed root>/run/static)
    
    *TODO: Add some instructions for nginx/apache* 

## Docker 

  *TODO*  

## config.yaml 

  *TODO - just copy the contents of config.example.yaml ? * 


