import struct
import numpy as np
from PIL import Image, ImageEnhance
 
def read_record(database,f):
    W, H = 64, 63
    if database == 'ETL8B2':
        s = f.read(512)
        r = struct.unpack('>2H4s504s', s)
        i1 = Image.frombytes('1', (W,H), r[3], 'raw')
        return r + (i1,)

    elif database == 'ETL1C':
        s = f.read(2052)
        r = struct.unpack('>H2sH6BI4H4B4x2016s4x', s)
        iF = Image.frombytes('F', (W,H), r[18], 'bit', 4)
        iP = iF.convert('P')

        enhancer = ImageEnhance.Brightness(iP)
        iE = enhancer.enhance(40)
        size_add = 12
        iE = iE.resize((W+size_add,H+size_add))
        iE = iE.crop((size_add/2,
                      size_add/2,
                      W + size_add/2,
                      H + size_add/2))
        return r + (iE,)

def get_ETL_data(dataset, categories, samplesPerCategory,
                 database='ETL8B2',
                 starting_writer=None,
                 vectorize=False, 
                 resize=None,
                 img_format=None,
                 get_scripts=False,
                 ):
    W, H = 64, 64
    new_img = Image.new('1', (W, H))

    if database == 'ETL8B2':
        name_base = 'ETLC/ETL8B/ETL8B2C'
    elif database == 'ETL1C':
        name_base = 'ETLC/ETL1/ETL1C_'

    try:
        filename = name_base+dataset
    except:
        filename = name_base+str(dataset)

    X = []
    Y = []
    scriptTypes = []

    try:
        iter(categories)
    except:
        categories = [categories]

    for id_category in categories:
        with open(filename, 'r') as f:
            if database == 'ETL8B2':
                f.seek((id_category * 160 + 1) * 512)
            elif database == 'ETL1C':
                f.seek((id_category * 1411 + 1) * 2052)

            for i in range(samplesPerCategory):
                try:
                    # skip records
                    if starting_writer:
                        for j in range(starting_writer):
                            read_record(database,f)
                    
                    # start outputting records
                    r = read_record(database,f)
                    new_img.paste(r[-1], (0,0))    

                    iI = Image.eval(new_img, lambda x: not x)

                    # resize images
                    if resize:
                        # new_img.thumbnail(resize, Image.ANTIALIAS)
                        iI.thumbnail(resize)
                        shapes = resize[0], resize[1]
                    else:
                        shapes = W, H
                    
                    # output formats
                    if img_format:
                        outData = iI
                    elif vectorize:
                        outData = np.asarray(iI.getdata()).reshape(shapes[0]*shapes[1])
                    else:
                        outData = np.asarray(iI.getdata()).reshape(shapes[0],shapes[1])
                    
                    X.append(outData)
                    if database == 'ETL8B2':
                        Y.append(r[1])
                        if id_category < 75:
                            scriptTypes.append(0)
                        else:
                            scriptTypes.append(2)
                    elif database == 'ETL1C':
                        Y.append(r[3])
                        scriptTypes.append(1)
                except:
                    print "Reached end of record"
                    break
    output = []
    if img_format:
        output += [X]
        output += [Y]
    else:
        X, Y = np.asarray(X, dtype=np.int32), np.asarray(Y, dtype=np.int32)
        output += [X]
        output += [Y]

    if get_scripts:
        output += [scriptTypes]

    return output
