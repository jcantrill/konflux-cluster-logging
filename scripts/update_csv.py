import os
from collections import OrderedDict
from sys import exit as sys_exit
from sys import stdout
from datetime import datetime
from ruamel.yaml import YAML

yaml = YAML()


def load_manifest(pathn):
   if not pathn.endswith(".yaml"):
      return None
   try:
      with open(pathn, "r") as f:
         return yaml.load(f)
   except FileNotFoundError:
      print("File can not found")
      exit(2)

def dump_manifest(pathn, manifest):
   with open(pathn, "w") as f:
      yaml.dump(manifest, f)
   return

def get_container(containers_array, container_name):
    for c_container in containers_array:
        if c_container['name'] == container_name:
            return c_container
    return None

csv_file = os.getenv('CSV_FILE')
upstream_csv = load_manifest(csv_file)

with open(os.getenv('VARS_FILE')) as pf:
    patches = yaml.load(pf)
    
    #update annotations
    upstream_annotations = upstream_csv['metadata']['annotations']
    for key in patches['annotations']:
        upstream_annotations[key] =  patches['annotations'][key]
    
    #update versions
    print("Patching metadata.name, spec.version, olm.skipRange using version:", patches['version'])
    upstream_csv['metadata']['name'] = "%s.v%s" % (patches['packageName'], patches['version'])
    upstream_csv['spec']['version'] =  patches['version']
    upstream_annotations['olm.skipRange'] = "%s <%s" % (patches['skipRange']['min'], patches['version'])

    # update deployed container spec
    upstream_containers = upstream_csv['spec']['install']['spec']['deployments'][0]['spec']['template']['spec']['containers']
    for container in patches['containers']:
       upstream_container = get_container(upstream_containers, container['name'])
       if upstream_container is None:
            print("container preset in patch, but not in upstream CSV", container['name'])
            exit(2)
       print("Patching deployment container:", container['name'])
       if container.get('image') is not None:
           upstream_container['image'] = container.get('image')

       if container.get('env') is not None:
           upstream_envs = upstream_container['env']
           for env in container.get('env'):
               print("Patching env:", env.get('name'))
               container_env = get_container(upstream_container['env'], env.get('name'))
               container_env['value'] = env.get('value')

    # update related images
    related_images = upstream_csv['spec']['relatedImages']
    for image in patches['releatedImages']:
       related_image = get_container(related_images, image['name'])
       if related_image is None:
            print("relatedImage preset in patch, but not in upstream CSV", related_image['name'])
            exit(2)
       print("Patching relatedImage:", related_image['name'])
       if image.get('image') is not None:
           related_image['image'] = image.get('image')

dump_manifest(csv_file, upstream_csv)