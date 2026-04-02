#written by Aexadev on 18/09/2025 - 28/12/2025 v1.5
from inc_noesis import *
import noesis, rapi # type: ignore
import struct, math


BUFFS = [
    b"pose",  # Pose / anim curves
    b"imag",  # Texture definitions
    b"mate",  # Materials
    b"ligh",  # Lights
    b"mode",  # Start of submesh list / geometry section
    b"verb",  # Submesh begin
    b"surf",  # Index buffer
    b"coor",  # Vertex buffer
    b"norm",  # Normal buffer
    b"tex0",  # UV0 buffer
    b"tex1",  # UV1 buffer
    b"colo",  # Vertex colors
    b"tan ",  # Tangent buffer
    b"weig",  # Weight buffer
    b"bone",  # Vertex bone indices
    b"skel",  # Skeleton
    b"base",  # Rest pose
    b"vere",  # Submesh end
    b"end ",  # File end
]

#TODO Fix texture name export 
#TODO Fix texture disappear on twice import
#TODO need major refactor of the asset type check
#TODO Fix axis weirdness in animat

def registerNoesisTypes():
    hMdl = noesis.register("PriNeo Model", ".bin~output")
    noesis.setHandlerTypeCheck(hMdl, ChkMdl)
    noesis.setHandlerLoadModel(hMdl, LoadMdl)
    
    hMdj = noesis.register("PriNeo Model", ".mdj")
    noesis.setHandlerTypeCheck(hMdj, ChkMdj)
    noesis.setHandlerLoadModel(hMdj, LoadMdj)
    
    hTex = noesis.register("PriNeo TexturePack", ".bin~output")
    noesis.setHandlerTypeCheck(hTex, ChkTex)
    noesis.setHandlerLoadRGBA(hTex, LoadTex)
    
    hCMdl = noesis.register("PriNeo Encrypted Model", ".bin")
    noesis.setHandlerTypeCheck(hCMdl, ChkCMdl)
    noesis.setHandlerLoadModel(hCMdl, LoadCMdl)
    
    hCTex = noesis.register("PriNeo Encrypted TexturePack", ".bin")
    noesis.setHandlerTypeCheck(hCTex, ChkCTex)
    noesis.setHandlerLoadRGBA(hCTex, LoadCTex)
    
    hssz = noesis.register("SynSophia archive", ".ssz")
    noesis.setHandlerTypeCheck(hssz, Chkssz)
    noesis.setHandlerExtractArc(hssz, Loadssz)
     
    hFnt = noesis.register("PriNeo Font", ".ssfont")
    noesis.setHandlerTypeCheck(hFnt, CheckSSFN)
    noesis.setHandlerLoadRGBA(hFnt,LoadSSFont)
    
    
    global LOAD_ANIMS
    LOAD_ANIMS = False                                        
    hAnimToggle = noesis.registerTool("Load animation", loadAnimToggle)
    noesis.setToolSubMenuName(hAnimToggle, "Prineo")
    noesis.checkToolMenuItem(hAnimToggle, LOAD_ANIMS)
    
    
    

    return 1



def loadAnimToggle(toolIndex):
    global LOAD_ANIMS
    LOAD_ANIMS = not LOAD_ANIMS
    noesis.checkToolMenuItem(toolIndex, LOAD_ANIMS)
    return 1
#SSZL
def Chkssz(data):
    bs = NoeBitStream(data)
    val = bs.readBytes(4)
    if val == b"SSZL":
        
        return 1
    else:
        return 0 
    
def Loadssz(fileName, fileLen, justChecking):
    data = rapi.loadIntoByteArray(fileName)
    bs  = NoeBitStream(data) 
    vr = bs.readBytes(4)  
    if vr != b"SSZL":
        noesis.doException("NOT SSZL!!")
    
    if justChecking:
        return 1   
    fdata = DecompressSSZL(data)
    rapi.exportArchiveFile(rapi.getExtensionlessName(rapi.getLocalFileName(rapi.getInputName()))+".dat", fdata)
    return 1

#SSfont
def CheckSSFN(data):
   bs = NoeBitStream(data) 
   bs.seek(8,NOESEEK_ABS)
   m = bs.readInt()
   if m == 152048384:
       return 1
   else:
       return 0
def LoadSSFont(data,texList):
    noesis.logPopup()
    bs = NoeBitStream(data)
    bs.seek(16,NOESEEK_ABS)
        
    for tIdx in range(bs.readInt()):
        HASH = bs.readUInt()
        print(hex(HASH))
        OFF = bs.readInt()
        SIZ = bs.readInt()
        here = bs.tell()
        bs.seek(OFF,NOESEEK_ABS)
        dta = bs.readBytes(SIZ)
        bs.seek(here,NOESEEK_ABS)
        
        bt = NoeBitStream(dta)
        bt.seek(1,NOESEEK_ABS)
        t1 = bt.readUShort()
        bt.readBytes(9)
        WIDTH = bt.readUShort()
        HEIGHT = bt.readUShort()
        print(t1,WIDTH,HEIGHT,OFF)
        if t1 == WIDTH == HEIGHT:
            bt.readBytes(2)
            idat = bt.readBytes(SIZ-18)
            rgba = rapi.imageDecodeRaw(idat, WIDTH, HEIGHT, "r8g8b8a8")
            tex = NoeTexture("_tex"+str(tIdx), WIDTH, HEIGHT, rgba, noesis.NOESISTEX_RGBA32)
            texList.append(tex)      
        elif t1 == 21316:#DDS
            texList.append(rapi.loadTexByHandler(dta,".dds"))
                     
    return 1       
#Decompressed model
def ChkMdl(data):
    bs = NoeBitStream(data)
    if bs.getSize() < 12:
        return 0
    id = bs.readBytes(4)
    
    if id not in BUFFS:
        bh = NoeBitStream(data)
        bh.seek(16, NOESEEK_ABS)
        FILE_COUNT = bh.readInt()
        
        if FILE_COUNT > 0:
            file_hash = bh.readInt()
            DATA_OFF  = bh.readInt()
            DATA_SIZ  = bh.readInt()

            here = bh.tell()
            bh.seek(DATA_OFF, NOESEEK_ABS)
            fileDat = bh.readBytes(DATA_SIZ)
            bh.seek(here, NOESEEK_ABS)
            bs = NoeBitStream(fileDat)
            id = bs.readBytes(4)
        
        
    if id in BUFFS:   
        return 1 
    else:
        return 0 
#-------------------------
#Original uncompressed model
def ChkMdj(data):
    bs = NoeBitStream(data)
    if bs.getSize() < 12:
        return 0
    val = bs.readBytes(4)
    return 1 if val in BUFFS else 0

def LoadMdj(data, mdl_list):
    return LoadMdl(data, mdl_list,1)
#--------------------------
#decompressed Texture pack
def ChkTex(data):
    bs = NoeBitStream(data)
    bs.seek(8,NOESEEK_ABS)
    val = bs.readUInt()
    if val == 152048384:
        if "_tex"in rapi.getInputName():
            return 1
    else:
        return 0 
#-------------------------
#Compressed model        
def ChkCMdl(data):
    bs = NoeBitStream(data)
    val = bs.readBytes(4)
    if val == b"SSZL":
        data = DecompressSSZL(data)
        return ChkMdl(data)
    
    else:
        return 0 
    
def LoadCMdl(data,mdl_list):
    data = DecompressSSZL(data)
    return LoadMdl(data, mdl_list,0)
#----------------------------------
#Compressed TexturePack    
def ChkCTex(data):
    bs = NoeBitStream(data)
    val = bs.readBytes(4)
    if val == b"SSZL":
        data = DecompressSSZL(data)
        
        return ChkTex(data)
    else:
        return 0 
    
def LoadCTex(data,tex_list):
    data = DecompressSSZL(data)
    return LoadTex(data, tex_list)
#---------------------------------
 
def LoadMdl(data, mdl_list,notPack=0,LoadTexDirect=False):#TODO add LoadAnimDirect
    
    modelFileDatas = []   #raw binary list of all the model streams in case of multipack
    texPck = None
    bs = NoeBitStream(data)
    
    
    if LoadTexDirect == False:  #wont be triggered if LoadMdl was called from LoadCtex for hashmap
        
        rapi.rpgCreateContext()
        noesis.logPopup() #TODO remove in release
        
        texPth = rapi.getExtensionlessName(rapi.getInputName())+"_tex_.bin"
        if rapi.checkFileExists(texPth):
            texPck = DecompressSSZL(rapi.loadIntoByteArray(texPth))
            HasTexures = True
        else:
            HasTexures = False
            print("Texture pack not found at:", texPth)
        
    
    #get all the model streams in the pack
    if notPack==0:#aka if this is a multipack
        bh = NoeBitStream(data)
        bh.seek(16, NOESEEK_ABS)
        FILE_COUNT = bh.readInt()
        print("[MultiPack]: Found", FILE_COUNT, "filestreams.")
        for mdlfile in range(FILE_COUNT):#TODO this is common reading for all multi stream files maybe unified function?
            file_hash = bh.readInt()
            DATA_OFF  = bh.readInt()
            DATA_SIZ  = bh.readInt()

            here = bh.tell()
            bh.seek(DATA_OFF, NOESEEK_ABS)
            fileDat = bh.readBytes(DATA_SIZ)
            modelFileDatas.append(fileDat)
            bh.seek(here, NOESEEK_ABS)
        #MODELFILE_COUNT = len(modelFileDatas)
            
            
    else:#single 
        modelFileDatas.append(data)
        
        

    for i, model in enumerate(modelFileDatas):
        bs = NoeBitStream(model)
        vBuf = iBuf = nBuf = uvBuf = uv1Buf =whBuf=biBuf= tnBuf =bytearray()
        FACE_COUNT = 0
        BONE_COUNT = 0
        skelChildCounts = []    
        skelNames       = []
    
        bBoneNames   = []
        bBoneMatrixes   = []
        animation = []
        bones = []        
        
        tetxures = []
        textureNames = []
        texture_ids = []
        textureSlots = []
        
        matList = []
        noeTextures = []
        
        poseBnames = []



        while bs.tell() < bs.getSize():

            tag = bs.readBytes(4)
            print("")
            print("///// READING CHUNK: "+tag.decode("ascii", "ignore")+" //////")

            #-------------------SKELETON-POSE/ANIMATION TRACKS--------------------------
            if tag == b"pose":
                
                poseName = _read_fixed_string(bs, bs.readUShort())                
                bs.readBytes(2)#data serialzier id
                pBoneCount = bs.readUShort()
                BONE_COUNT = pBoneCount
                bs.readBytes(8)

                kfBones = []
                maxTime = 0.0

                channels = ["Sx","Sy","Sz","Rx","Ry","Rz","Tx","Ty","Tz"]

                for i in range(pBoneCount):
                    bs.readBytes(2)
                    
                    pBoneName = _read_fixed_string(bs, bs.readUShort())
                    poseBnames.append(pBoneName)
                    
                    pBaseScale = NoeVec3.fromBytes(bs.readBytes(12))
                    pBaseRotat = NoeAngles.fromBytes(bs.readBytes(12))
                    pBaseTrasl = NoeVec3.fromBytes(bs.readBytes(12))


                    bs.readUInt()
                    pChannelMask   = bs.readUShort()

                    if pChannelMask == 0:
                        pass
                    curves = {}

                    for ci, ch in enumerate(channels):
                        if pChannelMask & (1 << ci):
                            kc = bs.readUInt()
                            keys = []
                            for _ in range(kc):
                                val = bs.readFloat()
                                t   = bs.readFloat()  # centiseconds
                                keys.append((t, val))
                                if t > maxTime:
                                    maxTime = t

                            
                            keys.sort(key=lambda kv: kv[0])
                            curves[ch] = keys


               
                


            #--------------------TEXURE-LIST---------------------------------
            
            elif tag == b"imag":
                TEX_COUNT = bs.readUShort()
                print("TEX_COUNT:",TEX_COUNT)
                for _ in range(TEX_COUNT):
                
                    unkt1 = bs.readUShort()
                    textureId = bs.readUInt()
                    imgName = _read_fixed_string(bs,bs.readShort())
                    textureNames.append(imgName)
                    textureSlots.append((textureId,imgName))
                    print("texture:", imgName, hex(SSFNV1a(rapi.getExtensionlessName(imgName))& 0xFFFFFFFF))
                
                if LoadTexDirect:#only when a texpack has been loaded directly
                    return textureNames
                
                if HasTexures:
                    for texIdx in range(len(textureNames)):
                        tetxures.append(GetTexture(texPck,textureNames[texIdx]))
                
                    
            #--------------------MATERIAL-PARAMETERS-----------------------        
            elif tag == b"mate":
                MAT_COUNT = bs.readUShort()

                for _ in range(MAT_COUNT):
                    tmap = []
                    datatype_id = bs.readUShort()
                    #print(bs.tell())
                    NAME = _read_fixed_string(bs, bs.readUShort())
                    print(NAME)

                    unkHash = bs.readUInt()  
                    #ambient
                    count = bs.readUShort()
                    for i in range(count):
                        type_id = bs.readUShort()  
                        print(type_id,"amb")
                        if type_id == 1029:
                            print("AMBIENT SLOT")
                            bs.readUInt()
                        else:
                            bs.readBytes(4)  

                    #diffuse
                    count = bs.readUShort()
                    for i in range(count):
                        type_id = bs.readUShort()
                        print(type_id,"dif")
                        if type_id == 1029:
                            print("DIFFUSE SLOT")
                            bs.readUInt()  
                        else:
                            bs.readBytes(4)

                    #specular
                    count = bs.readUShort()
                    for i in range(count):
                        type_id = bs.readUShort() 
                        print(type_id,"dif")
                        if type_id == 1029:
                            print("SPECULAR SLOT")
                            bs.readUInt()
                        else:
                            bs.readBytes(4)

                   
                    unk_float = 0
                    count = bs.readUShort()
                    for i in range(count):
                        print(type_id)
                        type_id = bs.readUShort() 
                        unk_float = bs.readUInt()  

                    
                    unk_float2 = 0
                    count = bs.readUShort()
                    for i in range(count):
                        print(type_id)
                        type_id = bs.readUShort()
                        unk_float2 = bs.readUInt()  

                    
                    some_string = None
                    sub_data = {}

                    if bs.readByte():
                        count = bs.readUShort()
                        for i in range(count):
                            type_id = bs.readUShort()
                            print(type_id)
                            txid= bs.readUInt()
                            texture_ids.append(txid)
                            
                            
                            #REMAP
                            for tid, name in textureSlots:
                                if (tid & 0xFFFFFFFF) == txid:
                                    tmap.append(name)
                                    print(name)

                        some_string = _read_fixed_string(bs, bs.readUShort())

                        sub_type = bs.readBytes(4)
                        if sub_type == b"MPSS":
                
                            for d in range(bs.readUShort()):
                                bs.readUShort()
                                bs.readBytes(16)
                        else:
                            bs.seek(-4, NOESEEK_REL)

                        sub_type = bs.readBytes(4)
                        if sub_type == b"MPDS":
                            for s in range(bs.readUShort()):
                                _read_fixed_string(bs, bs.readUShort())
                                bs.readBytes(32)
                        else:
                            bs.seek(-4, NOESEEK_REL)



                    mat = NoeMaterial(NAME, "")
                    if texPck and tmap:
                        if len(tmap) > 0:
                            n = addTexture(texPck, noeTextures, tmap[0])
                            if n: mat.setTexture(n)

                        if len(tmap) > 4:
                            n = addTexture(texPck, noeTextures, tmap[4])
                            if n: mat.setNormalTexture(n)

                        if len(tmap) > 3:
                            n = addTexture(texPck, noeTextures, tmap[3])
                            if n: mat.setSpecularTexture(n)
                    matList.append(mat)

               
            elif tag == b"ligh":
                for _ in range(bs.readUShort()):
                    bs.readUShort()
                    _read_fixed_string(bs,bs.readUShort())
                    bs.readBytes(49)
                
            
            #--------------------MODEL-METADATA-----------------------------
            
            elif tag == b"mode":
                while (bs.readUShort()==513):   
                    print(_read_fixed_string(bs,bs.readUShort()))
                    bs.readBytes(6)     
                    
                bs.seek(-2, NOESEEK_REL)

                fileEnd = False
                
                
                while (bs.tell() < bs.getSize() and fileEnd == False):
                    
                    bOffset = 0
                    while (bs.readUShort()==513):
                        print(_read_fixed_string(bs,bs.readUShort()))
                        bs.readBytes(6)
                        bOffset = bOffset +1     
                    bs.seek(-2, NOESEEK_REL)

                    #Mesh Header
                    
                    meshident = bs.readUShort()
                    
                    if (meshident!=515):
                        print("End of mesh buffers at offset ",bs.tell())
                        bs.seek(-2, NOESEEK_REL)
                        break
                    
                    MESH_NAME = _read_fixed_string(bs,bs.readUShort())
                    bs.readBytes(4)
                    boneMap = []
                    for _ in range(bs.readUShort()): 
                        bHash = bs.readUInt()  
                        for i, bName in enumerate(poseBnames):
                            if (SSFNV1a(bName)==bHash):
                                boneMap.append(int(i))
                                print(bName)
                                
                            
                            
                    bs.readFloat()
                    bs.readByte()
                    bs.readBytes(24)#AABB
                    
                    print("----------------------",MESH_NAME)
                    
                    meshEnd = False
                    #geoReader
                    while bs.tell() < bs.getSize() and meshEnd == False:
                        print("mesh while iter")
                        #
                        geobuf = bs.readBytes(4)
                        #--------------------GEOMETRY-BEGIN--------------------------    
                        if geobuf == b"verb":
                            print("-------------MESH_BEGIN----------------")
                            vBuf = iBuf = nBuf = uvBuf = uv1Buf =whBuf = biBuf = tnBuf= clBuf = b""
                            FACE_COUNT = 0
                            VERTEX_COUNT = 0
                            NORM_COUNT = 0
                            UV_COUNT = 0
                            UV1_COUNT = 0
                            TANG_COUNT = 0
                            WEIG_COUNT = 0
                            IBV_COUNT = 0
                            

                            
                        #------------------INDEX-BUFFER---------------------------------
                        elif geobuf == b"surf":
                            FACE_COUNT = bs.readUShort()
                            print("FACE_COUNT:",FACE_COUNT)
                            iBuf = bs.readBytes(FACE_COUNT * 6)
                        #------------------VERTEX-BUFFER--------------------------------
                        elif geobuf == b"coor":
                            VERTEX_COUNT = bs.readUShort()
                            print("VERTEX_COUNT:",VERTEX_COUNT)
                            vBuf = bs.readBytes(VERTEX_COUNT * 12)
                        #-----------------NORMAL-BUFFER---------------------------------
                        elif geobuf == b"norm":
                            NORM_COUNT = bs.readUShort()
                            print("NORM_COUNT:",NORM_COUNT)
                            nBuf = bs.readBytes(NORM_COUNT * 12)
                        #-----------------UV0-BUFFER---------------------------------
                        elif geobuf== b"tex0":
                            print("TEX0")
                            UV_COUNT = bs.readUShort()
                            uvBuf = bs.readBytes(UV_COUNT * 8)
                        #-----------------UV1-BUFFER---------------------------------
                        elif geobuf== b"tex1":
                            print("TEX1")
                            UV1_COUNT = bs.readUShort()
                            uv1Buf = bs.readBytes(UV1_COUNT * 8)
                        #-------------VERTEX-COLOR-----------------------------------
                        elif geobuf == b"colo":
                            clBuf = bs.readBytes(bs.readUShort()*4)
                        #-------------TANGENT-BUFFER---------------------------------    
                        elif geobuf== b"tan ":
                            TANG_COUNT = bs.readUShort()
                            print("TANG_COUNT",TANG_COUNT)
                            t3 = bs.readBytes(TANG_COUNT * 12)

                            import struct
                            t4 = bytearray(TANG_COUNT * 16)
                            mv3 = memoryview(t3)
                            mv4 = memoryview(t4)
                            for i in range(TANG_COUNT):
                                x, y, z = struct.unpack_from("<fff", mv3, i*12)
                                struct.pack_into("<ffff", mv4, i*16, x, y, z, 1.0)  # set w=+1

                            tnBuf = bytes(t4)

                        #-------------WEIGHT-BUFFER---------------------------------
                        elif geobuf== b"weig":
                            WEIG_COUNT = bs.readUShort()
                            print("WEIG_COUNT",WEIG_COUNT)
                            whBuf = bs.readBytes(WEIG_COUNT*16)
                            

                        #-------------BONEINDEX-BUFFER------------------------------
                        elif geobuf == b"bone":
                            IBV_COUNT = bs.readUShort()
                            print("IBV_COUNT", IBV_COUNT)

                            indices = [] 

                            for _ in range(IBV_COUNT):
                                for _ in range(4):
                                    idx = bs.readUByte()
                                    idx = (idx ) & 0xFF
                                    indices.append(idx)

                            biBuf = bytes(indices)  


                        #-------------GEOMETRY-END---------------------------------    
                        elif geobuf== b"vere":
                            print("-------------MESH_END----------------")
                            meshEnd = True
                            MAT_NAME_USED = _read_fixed_string(bs,bs.readUShort())
                            
                            print(MESH_NAME," material is: ",MAT_NAME_USED)
                            bs.readBytes(2)
                            
                            if vBuf and iBuf:
                                rapi.rpgClearBufferBinds()
                                rapi.rpgSetName(MESH_NAME)
                                rapi.rpgSetMaterial(MAT_NAME_USED) 
                                rapi.rpgBindPositionBuffer(vBuf, noesis.RPGEODATA_FLOAT, 12)
                                if whBuf:
                                    rapi.rpgSetBoneMap(boneMap)
                                    rapi.rpgBindBoneIndexBuffer(biBuf, noesis.RPGEODATA_UBYTE,4,4)
                                    rapi.rpgBindBoneWeightBuffer(whBuf, noesis.RPGEODATA_FLOAT,16,4)
                                if nBuf:
                                    rapi.rpgBindNormalBuffer(nBuf, noesis.RPGEODATA_FLOAT, 12)
                                if tnBuf:
                                    rapi.rpgBindTangentBuffer(tnBuf, noesis.RPGEODATA_FLOAT, 16)
                                if uvBuf:
                                    rapi.rpgBindUV1Buffer(uvBuf, noesis.RPGEODATA_FLOAT, 8)
                                if uv1Buf:
                                    rapi.rpgBindUV2Buffer(uv1Buf, noesis.RPGEODATA_FLOAT, 8)
                                if clBuf:
                                    rapi.rpgBindColorBuffer(clBuf, noesis.RPGEODATA_UBYTE, 4,4)
                                rapi.rpgCommitTriangles(iBuf, noesis.RPGEODATA_USHORT, FACE_COUNT*3, noesis.RPGEO_TRIANGLE)      
                            else:
                                print("no vertex or index buffer")
                            
                            break
                        
                        else:
                            unghk = "Unknown geometry chunk!! " + geobuf.split(b"\0", 1)[0].decode("ascii", "ignore")
                            noesis.doException(unghk)
                            break

            #-------------BNT-BUFFER--------------------------------
            elif tag== b"skel":
                skelChildCounts = []
                skelNames = []
                print("SKEL")
                for iBone in range(BONE_COUNT):
                    bs.readUShort()             
                    name = _read_fixed_string(bs, bs.readUShort())
                    bs.readInt()               
                    childCnt = bs.readUShort()         
                    skelNames.append(name)
                    skelChildCounts.append(childCnt)
                    
            
            #--------------BIND-POSE---------------------------------
            elif tag== b"base":
                baseName = _read_fixed_string(bs, bs.readUShort())
                BCount = bs.readUShort()
                print("BASE_COUNT",BCount)
                bBoneNames = []
                bBoneMatrixes = []
                for iBone in range(BCount):
                    _unk4 = bs.readUShort()                   
                    bname = _read_fixed_string(bs, bs.readUShort())
                    bScale = NoeVec3.fromBytes(bs.readBytes(12))
                    bRotat = NoeAngles.fromBytes(bs.readBytes(12))#degrees
                    bTrasl = NoeVec3.fromBytes(bs.readBytes(12))
                    
                    bMtx = bRotat.toMat43()
                    bMtx[0] *= bScale[0]  
                    bMtx[1] *= bScale[1] 
                    bMtx[2] *= bScale[2]  
                    bMtx[3] = bTrasl

                    bBoneNames.append(bname)
                    bBoneMatrixes.append(bMtx)
                
            

            elif tag == b"end ":
                print("-------------FILE_END----------------")
                break
                            
            else:
                
                noesis.doException("Unknown chunk!!")
                break
            


        if vBuf and iBuf:
            mdl = rapi.rpgConstructModel()
            mdl.setModelMaterials(NoeModelMaterials(noeTextures, matList))

            
        else:   
            mdl = NoeModel()
            
        
        
        names = poseBnames
        mats  = bBoneMatrixes 
        nBones = min(len(names), len(mats))
        if nBones > 0 and len(skelChildCounts) >= nBones:
            parentIdx = c2p(skelChildCounts[:nBones])

            for i in range(nBones):
                nm = names[i] 
                m  = mats[i]
                p  = parentIdx[i]
                bones.append(NoeBone(i, nm, m, None, p))

            if bones: 
                rapi.setPreviewOption("setSkelToShow", str(1))
                mdl.setBones(bones)

                try:
                    #animList = makeAnim(animation, bones, fps=60.0)
                    #if animList:
                    #    mdl.setAnims(animList)
                        #rapi.setPreviewOption("setAnimToShow", "0")
                    pass
                        
                
                except Exception as e:
                    print("Animation build failed:", e)
        #rapi.setPreviewOption("drawAllModels", "1")
        
            
        mdl_list.append(mdl)
    
        
        
    return 1

texCache = {}
def addTexture(texPck, texList, texName):
    key = rapi.getExtensionlessName(texName)
    if key in texCache:
        return key  

    tex = GetTexture(texPck, texName)
    if not tex:
        return None

    tex.name = key
    texList.append(tex)
    texCache[key] = tex
    return key


def GetTexture(texPck,texName):
        bt = NoeBitStream(texPck)
        bt.seek(16,NOESEEK_ABS)
        
        for tIdx in range(bt.readInt()):
            HASH = bt.readUInt()
            
            OFFSET = bt.readUInt()
            SIZE = bt.readUInt()
            here = bt.tell()
            
            #get texture 
            bt.seek(OFFSET,NOESEEK_ABS)
            hd = bt.readBytes(3)
            bt.seek(-3,NOESEEK_REL)
            if HASH == SSFNV1a(rapi.getExtensionlessName(texName)):
                texRaw = bt.readBytes(SIZE)
                if hd == b"DDS":
                    rgba = rapi.loadTexByHandler(texRaw, ".dds")
                    rgba.name = rapi.getExtensionlessName(texName)
                    
                else:
                    
                    rgba = rapi.loadTexByHandler(texRaw, ".tga")
                    rgba.name = rapi.getExtensionlessName(texName)
                    
                    
                print("[GetTexture] found texture:  ", texName, "hash: ", hex(HASH))
                return rgba
            bt.seek(here,NOESEEK_ABS)
            
        print("[GetTexture] texture NOT found :  ", texName, "hash: ", hex(SSFNV1a(texName)))
        #TODO add support for external texpak
        
        

def LoadTex(data,texList):
    texnames = None
    #need to get the texture names from the model first
    mdlPth_a = rapi.getExtensionlessName(rapi.getInputName())[:-5]+".bin"
    mdlPth_b = rapi.getExtensionlessName(rapi.getInputName())[:-5]+".mdj"
    
    if rapi.checkFileExists(mdlPth_a):  
        
        texnames = LoadMdl(DecompressSSZL(rapi.loadIntoByteArray(mdlPth_a)),None,0,True)
    elif rapi.checkFileExists(mdlPth_b):
        texnames = LoadMdl(rapi.loadIntoByteArray(mdlPth_b),None,1,True) 

    bs = NoeBitStream(data)
    
    if texnames:
        for tIdx in range(len(texnames)):
            tex = GetTexture(data,texnames[tIdx])
            if tex:
                tex.name = rapi.getExtensionlessName(texnames[tIdx])
                texList.append(tex)
    else:
        VERSION = bs.readUInt()
        FILE_SIZE = bs.readUInt()
        tex_ident = bs.readUInt()
        unk = bs.readUInt()
        TEXTURE_COUNT = bs.readUInt()
        print(unk, TEXTURE_COUNT)
        
        for _ in range(TEXTURE_COUNT):
            ID = bs.readUInt()
            
            OFFSET = bs.readUInt()
            SIZE = bs.readUInt()
            here = bs.tell()
            
            #get texture 
            bs.seek(OFFSET,NOESEEK_ABS)
            hd = bs.readBytes(3)
            bs.seek(-3,NOESEEK_REL)
            texRaw = bs.readBytes(SIZE)
            if hd == b"DDS":
                tex = rapi.loadTexByHandler(texRaw, ".dds")
            else:
                
                tex = rapi.loadTexByHandler(texRaw, ".tga")
            bs.seek(here,NOESEEK_ABS)
            texList.append(tex)
            print("texture:",hex(ID), "off",OFFSET,"siz",SIZE)

    return 1



def makeAnim(animationClips, bones, fps=60.0):
    if not animationClips or not bones:
        return []

    nameToIndex = {b.name: i for i, b in enumerate(bones)}
    channels = ["Sx","Sy","Sz","Rx","Ry","Rz","Tx","Ty","Tz"]

    animList = []

    for clipIdx, (poseName, animBones, maxTimeCs) in enumerate(animationClips):
        kfBones = []

        for ab in animBones:
            bname = ab.get("name", "")
            if bname not in nameToIndex:
                continue

            boneIdx = nameToIndex[bname]
            baseS = ab.get("baseS", (1.0, 1.0, 1.0))
            baseR = ab.get("baseR", (0.0, 0.0, 0.0))
            baseT = ab.get("baseT", (0.0, 0.0, 0.0))
            curves = ab.get("curves", {})

            if not curves:
                continue

            # channel -> {t_cs: val}
            cMaps = {}
            for ch in channels:
                if ch in curves:
                    d = {}
                    for t, v in curves[ch]:
                        d[t] = v
                    cMaps[ch] = d

            if not cMaps:
                continue

            hasS = any(k in cMaps for k in ("Sx","Sy","Sz"))
            hasR = any(k in cMaps for k in ("Rx","Ry","Rz"))
            hasT = any(k in cMaps for k in ("Tx","Ty","Tz"))

            allTimes = set()
            for d in cMaps.values():
                allTimes.update(d.keys())

            if not allTimes:
                continue

            times = sorted(allTimes)

            sKeys = []
            rKeys = []
            tKeys = []

            for t_cs in times:
                
                frameTime = float(t_cs) * 0.01

                sx, sy, sz = baseS
                rx, ry, rz = baseR
                tx, ty, tz = baseT

                if "Sx" in cMaps and t_cs in cMaps["Sx"]: sx = cMaps["Sx"][t_cs] 
                if "Sy" in cMaps and t_cs in cMaps["Sy"]: sy = cMaps["Sy"][t_cs] 
                if "Sz" in cMaps and t_cs in cMaps["Sz"]: sz = cMaps["Sz"][t_cs] 

                if "Rx" in cMaps and t_cs in cMaps["Rx"]: rx = cMaps["Rx"][t_cs] * noesis.g_flRadToDeg
                if "Ry" in cMaps and t_cs in cMaps["Ry"]: ry = cMaps["Ry"][t_cs] * noesis.g_flRadToDeg
                if "Rz" in cMaps and t_cs in cMaps["Rz"]: rz = cMaps["Rz"][t_cs] * noesis.g_flRadToDeg

                if "Tx" in cMaps and t_cs in cMaps["Tx"]: tx = cMaps["Tx"][t_cs]
                if "Ty" in cMaps and t_cs in cMaps["Ty"]: ty = cMaps["Ty"][t_cs] 
                if "Tz" in cMaps and t_cs in cMaps["Tz"]: tz = cMaps["Tz"][t_cs] 

                if hasS:
                    #sKeys.append(NoeKeyFramedValue(frameTime, NoeVec3((sx, sy, sz))))
                    pass
                if hasR:
                    rKeys.append(NoeKeyFramedValue(frameTime, NoeVec3((rx, ry, rz))))
                if hasT:
                    tKeys.append(NoeKeyFramedValue(frameTime, NoeVec3((tx, ty, tz))))

            kfb = NoeKeyFramedBone(boneIdx)

           
            if rKeys:
                kfb.setRotation(rKeys, noesis.NOEKF_ROTATION_EULER_XYZ_3)

            if sKeys:
                kfb.setScale(sKeys, noesis.NOEKF_SCALE_VECTOR_3)


            if tKeys:
                kfb.setTranslation(tKeys, noesis.NOEKF_TRANSLATION_VECTOR_3)

            #kfb.flags |= noesis.KFBONEFLAG_MODELSPACE
            #kfb.flags |= noesis.KFBONEFLAG_ADDITIVE
            kfBones.append(kfb)

        if kfBones:
            animList.append(NoeKeyFramedAnim("anim", bones, kfBones, 60))

    return animList


def _read_fixed_string(bs, n):
    raw = bs.readBytes(n)
    return noeAsciiFromBytes(raw)


def c2p(childCounts):
    n = len(childCounts)
    parents = [-1] * n
    stack = []
    for i in range(n):
     
        while stack and stack[-1][1] == 0:
            stack.pop()
        if stack:
            parents[i] = stack[-1][0]

            stack[-1] = (stack[-1][0], stack[-1][1] - 1)
        else:
            parents[i] = -1
        cnt = childCounts[i] if i < len(childCounts) else 0
        stack.append((i, cnt))
    return parents


# comp types
ZLIB = 0
GZIP = 1
# enc types
MT_XOR = 31

def DecompressSSZL(data: bytes) -> bytes:
    print("Decompressing...")
    bs = NoeBitStream(data)

    bs.seek(4, NOESEEK_ABS)

    VERSION   = bs.readUInt()
    RSIZE = bs.readUInt()

    # read the 8 control bytes
    FLAGS = bs.readBytes(8)

    comp_flag     = FLAGS[0]
    comp_type     = FLAGS[1]
    reservedb     = FLAGS[2]
    enc_type      = FLAGS[3]
    reserved_zero = (FLAGS[4:] == b"\x00\x00\x00\x00")

    scheme_control_bytes = (
        comp_flag in (0, 1) and
        comp_type in (0, 1) and
        reservedb == 0 and
        enc_type in (0, MT_XOR) and
        reserved_zero
    )

    if scheme_control_bytes:
        is_encrypted  = (enc_type == MT_XOR)
        is_compressed = (comp_flag != 0)
        use_gzip      = (comp_type == GZIP)
    else:
        opts = (
            FLAGS[0] |
            (FLAGS[1] << 8) |
            (FLAGS[2] << 16) |
            (FLAGS[3] << 24)
        )
        is_compressed = bool(opts & 0x00000001)
        use_gzip      = bool(opts & 0x00000002)
        is_encrypted  = bool(opts & 0x80000000)

    
    compdta = bs.readBytes(bs.getSize() - bs.tell())

    if is_encrypted:
        compdta = bytes(MT1997(bytearray(compdta), 0x40C360F3))

    if is_compressed:

        if len(compdta) >= 2 and compdta[0] == 0x1F and compdta[1] == 0x8B:
            use_gzip = True

        wbits = 31 if use_gzip else 15
        out = rapi.decompInflate(compdta, RSIZE, wbits)
        print("Decompress done!")
        return out
    else:
        return compdta


def MT1997(buf: bytearray, seed: int) -> bytearray:
    print("Decrypting...")
    N = 624
    MASK = 0x7FFFFFFF
    MULT = 0x13F8769B
    T = 0x1908B0DF
    B = 0xFF3A58AD
    C = 0xFFFFDF8C

    mt = [0] * N
    mt[0] = seed & MASK
    for i in range(N - 1):
        cur = mt[i]
        tmp = cur ^ (cur >> 30)
        mul = (MULT * (tmp & 0xFFFFFFFF)) & 0xFFFFFFFF
        mt[i + 1] = ((i + 1) - mul) & MASK

    index = 0

    def next_u32():
        nonlocal index
        a = mt[index]
        b = mt[(index + 1) % N]
        c = mt[(index + 397) % N]
        part = (a ^ ((a ^ b) & MASK)) >> 1
        mt[index] = (part ^ c ^ (T * (b & 1))) & MASK
        val = mt[index]
        index = (index + 1) % N
        t1 = (val >> 11) ^ val
        t2 = ((t1 & B) << 7) & 0xFFFFFFFF
        t3 = t1 ^ t2
        t4 = ((t3 & C) << 15) & 0xFFFFFFFF
        t5 = t3 ^ t4

        s = t5 & 0xFFFFFFFF
        if s & 0x80000000:         
            s -= 0x100000000
        v = (s ^ (s >> 18)) & MASK
        return v

    n = len(buf)
    full = n // 4
    rem = n & 3
    for i in range(full):
        v = struct.unpack_from("<I", buf, i * 4)[0]
        v ^= next_u32()
        struct.pack_into("<I", buf, i * 4, v & 0xFFFFFFFF)
    if rem:
        nxt = next_u32()
        base = full * 4
        for i in range(rem):
            buf[base + i] ^= (nxt >> (8 * i)) & 0xFF
    print("Decrypting done!")

    return buf

def SSFNV1a(a1: str) -> int:
    if isinstance(a1, str):
        a1 = a1.encode("latin1")

    FNV_CONST = 0x811C9DC5
    result = 0

    for b in a1:
        result = (b ^ ((FNV_CONST * result) & 0xFFFFFFFF)) & 0xFFFFFFFF

    return result

    
    




    
