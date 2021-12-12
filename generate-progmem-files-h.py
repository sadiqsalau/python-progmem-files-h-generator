#!/usr/bin/env python3
import os
import sys
import glob
import hashlib
import mimetypes
import argparse
from textwrap import indent, dedent

def main():
	print("<<PROGMEM_Files.h Generator>>\n")

	args=collect_args()

	folder=args.folder
	output=args.output

	if not os.path.isdir(folder):
		print(f"The folder {folder} does not exists!")
	else:
		generate_progmem_files_h(folder, output)


def collect_args():
	parser = argparse.ArgumentParser(description='Generates a PROGMEM_Files header file')
	parser.add_argument(
		'--folder',
        type=str,
		default="public",
        help='the folder to scan - default is \"public\"'
   )

	parser.add_argument(
		'--output',
		type=str,
		default="PROGMEM_Files.h",
		help="the output file - default is \"PROGMEM_Files.h\"",
	)
	return parser.parse_args()



def generate_progmem_files_h(folder, output):
	print(f"Collecting files from {folder}...")

	files=collect_files_data(folder)

	print(f"Found {len(files)} file(s)")
	print(f"Generating header file..")

	print(f"Saving to {output}")
	with open(output, "w") as output:
		output.write(cpp_init())
		output.write(cpp_progmem_files_declare(files))
		output.write(cpp_progmem_files_list(files))
		output.write(cpp_get_progmem_file_func())
		output.close()

	print(f"Successfully generated header file..")


def cpp_init():
	return dedent("""
		
		typedef struct {
			const char* name;
			const char* mime;
			const char* data;
			size_t size;
		} PROGMEM_File;


	""")

def cpp_progmem_files_list(files):
	return dedent("""

		const PROGMEM_File progmem_files[] PROGMEM = {{
		{0}
		}};
		
		const size_t PROGMEM_FILES_COUNT PROGMEM = sizeof(progmem_files) / sizeof(PROGMEM_File);

	""").format(
		indent(",\n".join([cpp_progmem_file_struct(file) for file in files]), "\t")
	)


def cpp_get_progmem_file_func():
	return dedent("""
		const PROGMEM_File* getPROGMEM_File(const char* filename)
		{
			const PROGMEM_File* res=nullptr;
			for(int i=0; i<PROGMEM_FILES_COUNT; i++)
			{
				if(String(progmem_files[i].name).equals(filename))
				{
					res=&progmem_files[i];
					break;
				}
			}
			return res;
		}
	""")



def cpp_progmem_file_struct(file):
	return dedent(f"""
		
		{{
			name: {cpp_progmem_file_key(file, "name")},
			mime: {cpp_progmem_file_key(file, "mime")},
			data: {cpp_progmem_file_key(file, "data")},
			size: sizeof({cpp_progmem_file_key(file, "data")}),
		}}

	""").strip()




def cpp_progmem_files_declare(files):
	return "\n\n".join(
		[cpp_progmem_file(file) for file in files]
	)



def cpp_progmem_file(file):
	return "\n".join([
		cpp_progmem_file_name(file),
		cpp_progmem_file_type(file),
		cpp_progmem_file_data(file)
	])




def cpp_progmem_file_key(file, key): 
	return f"""progmem_file_{get_md5(file["name"].encode())}_{key}"""
def cpp_progmem_file_rawliteral(file, key): 
	return fr"""const char {cpp_progmem_file_key(file, key)}[] PROGMEM = R"rawliteral({file[key]})rawliteral";"""


def cpp_progmem_file_name(file): return cpp_progmem_file_rawliteral(file, "name")
def cpp_progmem_file_type(file): return cpp_progmem_file_rawliteral(file, "mime")
def cpp_progmem_file_data(file): 
	return fr"""const char {cpp_progmem_file_key(file, "data")}[] PROGMEM = {{{",".join(file["data"])}}};"""



def collect_files_data(folder):
	return [
		{
			"name": file, 
			"mime": get_file_mime(file),
			"data": read_bytes_to_hex_list(folder + file)
		} 
		for file in scanfiles(folder)
	]



def scanfiles(folder, base="/"):
	path=folder + base # Current folder from base
	results=[] # The list to hold the files

	for entry in os.scandir(path):
		name=base + entry.name
		if entry.is_dir():
			results += scanfiles(folder, name + "/")
		else:
			results.append(name)
			print("===>" + name)

	return results



def read_bytes_to_hex_list(path):
	with open(path, "rb") as handle:
		return [hex(b) for b in handle.read()]


def get_md5(string):
	h=hashlib.new("md5")
	h.update(string)
	return h.hexdigest()


def get_file_mime(file):
	mimetypes.init()
	ftype, fencoding = mimetypes.guess_type(file)

	return ftype or "application/octet-stream"

main()