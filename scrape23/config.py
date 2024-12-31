import tomllib

print ("Loading configuration file")
data = []
with open("./scrape23.toml", "rb") as f:
    data = tomllib.load(f)

archive_path = data['common']['archivepath']
feed_directory = data['common']['feeddir']
feed_url = data['common']['feedurl']
feeds = data['feeds']

for key in feeds:
    print(key)
    
