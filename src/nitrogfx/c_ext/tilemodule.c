#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdio.h>

/*C implementations for tile-related hotspots*/


#define ASSERT(cond, msg) if(!(cond)){ \
			PyErr_SetString(PyExc_ValueError, msg); \
			return NULL; \
		}


// _4bpp_to_8bpp(input : bytes) -> bytes
static PyObject* _4bpp_to_8bpp(PyObject *self, PyObject *args){
	const unsigned char* input;
	Py_ssize_t input_len;
	
	if(!PyArg_ParseTuple(args, "y#", &input, &input_len))
		return NULL;
	
	char* output = PyMem_Malloc(2*input_len);
	int j = 0;
	for(int i = 0;i<input_len;i++){
		output[j++] = input[i] & 0xF;
		output[j++] = input[i] >> 4;
	}
	
	return PyBytes_FromStringAndSize(output, 2*input_len);
}


// _8bpp_to_4bpp(input : bytes) -> bytes
static PyObject* _8bpp_to_4bpp(PyObject *self, PyObject *args){
	const unsigned char* input;
	Py_ssize_t input_len;
	
	if(!PyArg_ParseTuple(args, "y#", &input, &input_len))
		return NULL;
	
	char* output = PyMem_Malloc(input_len / 2);
	int j = 0;
	for(int i = 0;i<input_len/2;i++){
		output[i] = (input[j] & 0xF) | (input[j+1] << 4);
		j += 2;
	}
	
	return PyBytes_FromStringAndSize(output, input_len / 2);
}


// flip_tile_data(input : bytes, hflip : bool, vflip : bool) -> bytes
static PyObject* flip_tile_data(PyObject *self, PyObject *args){
	const unsigned char* input;
	Py_ssize_t input_len;
	int hflip, vflip;

	if(!PyArg_ParseTuple(args, "y#pp", &input, &input_len, &hflip, &vflip))
		return NULL;
	
	ASSERT(input_len == 64, "Tiles must be 64 bytes long.");

	char* output = PyMem_Malloc(64);
	for(int y = 0; y<8;y++){
		for(int x = 0; x<8;x++){
			int x2 = hflip ? 7-x : x;
			int y2 = vflip ? 7-y : y;
			output[8*y2+x2] = input[8*y+x];
		}
	}
	return PyBytes_FromStringAndSize(output, 64);
}


// read_ncbr_tile(data : bytes, tilenum : int, bpp : int, width : int) -> bytes
static PyObject* read_ncbr_tile(PyObject *self, PyObject *args){
	const unsigned char* data;
	Py_ssize_t data_len;
	unsigned int tilenum, bpp, width;
	
	if(!PyArg_ParseTuple(args, "y#III", &data, &data_len, &tilenum, &bpp, &width))
		return NULL;
	
	int x = tilenum % width;
	int y = tilenum / width;
	int k = 0;
	char* output = PyMem_Malloc(64);
	int offset = x*4 + 4*y*width*8;
	if(bpp == 8){
		ASSERT(data_len >= 2*offset + 7*width + 8, "8bpp data is too short.");
		for(int i = 0;i<8;i++){
			for(int j = 0;j<8;j++){
				output[k++] = data[2*offset + i*width + j];
			}
		}
	}else{
		ASSERT(data_len >= offset + 4*7*width + 4, "4bpp data is too short.");
		for(int i = 0;i<8;i++){
			for(int j = 0;j<4;j++){
				unsigned char val = data[offset+j];
				output[k++] = val & 0xf;
				output[k++] = val >> 4;
			}
			offset += 4*width;
		}
	}
	return PyBytes_FromStringAndSize(output, 64);
}



static void plot_tile(char* dst, int x, int y, char* tile, int width){
	int k = 0;
	for(int i = 0;i < 8; i++){
		for(int j = 0;j < 8; j++){
			dst[width*(i+y) + (j+x)] = tile[k++];
		}
	}
}

// pack_ncbr_tiles(tiles : list of bytes, width : int, height : int)
static PyObject* pack_ncbr_tiles(PyObject *self, PyObject *args){
	PyObject* tiles;
	unsigned int width, height;
	
	if(!PyArg_ParseTuple(args, "OII", &tiles, &width, &height))
		return NULL;

	char* output = PyMem_Malloc(width * height * 64);
	unsigned int x = 0;
	unsigned int y = 0;
	for(unsigned int i = 0;i<width*height;i++){
		PyObject* tile = PyList_GetItem(tiles, i);
		if(!tile) return NULL;
		
		char* tiledata;
		Py_ssize_t tilelen;
		
		ASSERT(PyBytes_Check(tile), "List contained something other than bytes");
		PyBytes_AsStringAndSize(tile, &tiledata, &tilelen);
		ASSERT(tilelen == 64, "Tiles should be 64 bytes long");	
		
		plot_tile(output, x, y, tiledata, width*8);
		x += 8;
		if(x >= width*8){
			x = 0;
			y += 8;
		}
	}

	return PyBytes_FromStringAndSize(output, width*height*64);
}


// draw_tile_to_buffer(bytearray, tile : bytes, x : int, y : int, buffer_width : int)
static PyObject* draw_tile_to_buffer(PyObject *self, PyObject *args){
	PyObject* bytearray;
	char *buffer, *tile;
	unsigned int width, x, y;
	Py_ssize_t tile_size;
	
	if(!PyArg_ParseTuple(args, "Yy#III", &bytearray, &tile, &tile_size, &x, &y, &width))
		return NULL;
	ASSERT(tile_size == 64, "Tile is not 64 bytes");
	ASSERT((y+7)*width + (x+8) <= PyByteArray_Size(bytearray), "Buffer is too small");
	buffer = PyByteArray_AS_STRING(bytearray);
	plot_tile(buffer, x, y, tile, width);
	Py_RETURN_NONE;
}


static PyMethodDef tileMethods[] = {
    {"_4bpp_to_8bpp", (PyCFunction)_4bpp_to_8bpp, METH_VARARGS, "Convert 4bpp bytes to 8bpp"},
    {"_8bpp_to_4bpp", (PyCFunction)_8bpp_to_4bpp, METH_VARARGS, "Convert 8bpp bytes to 4bpp"},
    {"flip_tile_data", (PyCFunction)flip_tile_data, METH_VARARGS, "Flip a tile"},
    {"read_ncbr_tile", (PyCFunction)read_ncbr_tile, METH_VARARGS, "Read a tile from ncbr"},
    {"pack_ncbr_tiles", (PyCFunction)pack_ncbr_tiles, METH_VARARGS, "Pack list of bytes into ncbr"},
    {"draw_tile_to_buffer", (PyCFunction)draw_tile_to_buffer, METH_VARARGS, "Blit a tile to a bytearray"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef tilemodule = {
    PyModuleDef_HEAD_INIT,
    "tile",
    "Tile functions.",
    -1,
    tileMethods
};

PyMODINIT_FUNC PyInit_tile(void)
{
    return PyModule_Create(&tilemodule);
}

