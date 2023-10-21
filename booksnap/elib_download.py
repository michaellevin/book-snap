import os
import json
import glob
import time

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


temp_folder = 'C:/tempRender'

def download(pth, download = True):
	cmd = 'curl {}'.format(pth)
	#j = urlopen(pth)
	time.sleep(90)
	output, success = system_call(cmd)
	name = output.split('<title>')[1].split('</title>')[0].strip().replace(' ', '_').replace('|', '').replace(':', '').replace('__', '').replace('.', '').replace(',', '')
	pprint(name)
	time.sleep(90)
	ids = str(output).split('links_z0":{')[1].split('}')[0]
	ids = eval('{' + ids + '}')
	list_of_ids = list(ids.keys())
	dest_folder = 'F:/prlib/{}/'.format(name)
	if download:
		if not os.path.exists(dest_folder):
			os.makedirs(dest_folder)
		for i, im in enumerate(list_of_ids[4:-7]):
			im_address = 'http://elib.shpl.ru/pages/{}/zooms/6'.format(im)
			im_cmd = 'curl {} -o {}/tmp_{}.jpeg'.format(im_address, temp_folder, str(i + 1).zfill(3))
			print(im_cmd)
			system_call(im_cmd)
			if i != len(list_of_ids)-1:
				time.sleep(90)

	# create pdf
	imgs = glob.glob("{}/*.jpeg".format(temp_folder))
	with open("{}/{}.pdf".format(dest_folder, name),"wb") as f:
		f.write(img2pdf.convert(imgs))
	for i in imgs[-1::-1]:
		os.remove(i)


pth = 'http://elib.shpl.ru/ru/nodes/64875'
#pth = 'http://elib.shpl.ru/ru/nodes/17829-t-2-s-1-yanvarya-po-1-iyulya-1916-goda-1916'
#pth = 'http://elib.shpl.ru/ru/nodes/3541-futuristy-pervyy-zhurnal-russkih-futuristov-1-2-m-1914'
download(pth, download = True)