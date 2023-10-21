import os
import json
import glob

from subprocess import check_output, CalledProcessError, STDOUT
from pprint import pprint
from urllib.request import urlopen
from posixpath import join
import img2pdf

def system_call(command):
    try:
        output = check_output(command, stderr=STDOUT).decode()
        success = True 
    except CalledProcessError as e:
        output = e.output.decode()
        success = False
    return output, success


DEZOOMIFY_PTH = "C:/gg/prlib/dezoomify-rs.exe"

def create_pdf(dest_folder, name):
	imgs = glob.glob("{}/*.jpeg".format(dest_folder))
	with open("{}/{}.pdf".format(dest_folder, name),"wb") as f:
		f.write(img2pdf.convert(imgs))
	for i in imgs[-1::-1]:
		os.remove(i)

# DOWNLOAD
def download(pth, download = True):
	id_ = pth.split('/')[-1]
	cmd = 'curl {}'.format(pth)
	output, success = system_call(cmd)

	js = output.split('.json"')[0].split('https')[-1]
	js_cmd = 'https{0}.json'.format(js).replace('\\', '')
	j = urlopen(js_cmd)
	#pprint(json_output)
	data = json.load(j)
	all_images = [dct['f'] for dct in data['pgs']]
	ids = js.replace('\\', '').split('/')[-3:-1]
	#pprint(all_images)
	name = output.split('<meta itemprop="name" content="')[1].split('"')[0].replace(' ', '_')
	dest_folder = 'C:/gg/prlib/{}/'.format(name)
	if download:
		if not os.path.exists(dest_folder):
			os.makedirs(dest_folder)
		for i, im in enumerate(all_images):
			im_address = 'https://content.prlib.ru/fcgi-bin/iipsrv.fcgi?FIF=/var/data/scans/public/{}/{}/{}&JTL=2,0&CVT=JPEG'.format(*ids, im)
			print('{}/{}  >  '.format(i, len(all_images)), im_address)
			system_call('{} -l {} {}.jpeg'.format(DEZOOMIFY_PTH, im_address, join(dest_folder, str(i).zfill(3))))
	
	# create pdf
	create_pdf(dest_folder, name)
	
#pth = 'https://www.prlib.ru/node/335775'
#pth = 'https://www.prlib.ru/item/360808'
#pth = 'https://www.prlib.ru/item/362974'
#pth = 'https://www.prlib.ru/item/322979'
#https://www.prlib.ru/item/1176322
for i in [389338,]: 
	pth = 'https://www.prlib.ru/item/{}'.format(i)
	download(pth, download = True)

#create_pdf("F:/prlib/Великая_война_в_картинка_и_образах", "Великая_война_в_картинка_и_образах")