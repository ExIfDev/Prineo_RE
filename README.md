## About

PriPara (internal name Prineo) is an arcade rythm game developed by SynSophia.

## Goal

The goal of this project was to reverse the model format of the arcade series in order to port exclusive characters to the newer version of game on Nintendo Switch.

## Screenshots

Some interesting screenshots taken during the RE process.

---

![Early Noesis addon import](https://github.com/user-attachments/assets/36790abf-1f46-4521-85fb-b0fd4280f1a0)
*Early version of the Noesis addon — first partial model import (14-09-2025)*

---

![C# model reader](https://github.com/user-attachments/assets/f764ebda-b4bc-4e2a-ac4c-c6aecb2ef540)
*C# model reader used to test deserialization implementations (06-12-2025)*

---

![Hooking hashing function](https://github.com/user-attachments/assets/191ff9d1-b48a-42c2-9fb2-3bd727042521)
*Running a decrypted dump in a VM and hooking the hashing function via DLL injection using MinHook and Xenos, using the ReturnAddress intrinsic to track hash function calls (08-12-2025)*

---

![Imported scene](https://github.com/user-attachments/assets/3dd5f690-bb5f-4906-a120-d18a222b21cc)
*Imported scene from the game via the Noesis addon (27-12-2025)*




## Custom Crypto Implementations

The game implements modified versions of standard cryptographic primitives.

---

### 1. FNV-1

- reversed order of operation
- missing initial offset basis

**Implementation:**
https://github.com/ExIfDev/Prineo_RE/blob/main/Noesis/fmt_prineo.py#L1130-L1140

---

### 2. Mersenne Twister

- Subtracts instead of addition
- Custom multiplier *0x13F8769B*
- masked to 31 bits
- Mutated twist op with custom const
- Modified mask constants 

**Implementation:**
https://github.com/ExIfDev/Prineo_RE/blob/main/Noesis/fmt_prineo.py#L1074-L1128

## FILE FORMAT RESEARCH

- Game: PriPara (Prineo)
- Handedness: right handed 
- Endianness: LE
- Triangle Winding: CW
- Type: sparse chunk
- MaxPolyC: 65535
- MaxBoneC: 255


The following documentation refers to files after SSZL decompression.

## .BIN  (GENERIC CONTAINER)
```c#
const byte[] ident = {0x00, 0x13, 0x10, 0x09};
struct Header
{
    uint32 VERSION;//1
    uint32 FILE_SIZE;
    byte[4] Ident;
    int32 unk1;
    int32 unk2;
    int32 unk3;
    uint32 DATA_OFFSET; //absolute offset
    uint32 DATA_SIZE;
};


```
## .MDJ
```c#
//the MDJ file can contain a variety of buffers related to geometry and scenes, it does
//not have a header, its assumed to start with one of the following buffers
//and always terminate with the "end/0/" marker


struct Pose //pose applied to a skeleton (=restPose in a model container) 
            //usually this pose is the same as in the "base" buffer.
            //if AnimParams are present then what follows is the animation curves.
            //AnimParams can be null when there are no keyframes.
{
    char[4] ident = "pose";
    uint16 strLen;
    char[strLen] POSE_NAME;
    byte[2] unk;
    uint16 BONE_COUNT;
    byte[8] unkdata;

    struct Bone[BONE_COUNT]
    {
        uint16 serializer_id;//518
        uint16 strLen;
        string[strLen] BONE_NAME;
        //Base transform
        float sclX, sclY, sclZ;
        float rotX, rotY, rotZ;
        float tslX, tslY, tslZ;

        //for all channels (9) "Sx", "Sy", "Sz", "Rx", "Ry", "Rz", "Tx", "Ty", "Tz"

        struct AnimationParams //6 bytes
        {
            uint16 unk2; //possibly an uint32 since unk3 is always 0
            uint16 unk3;
            uint16 CHANNEL_MASK;
        };
        //if anim params are not null then....
        uint32 KEYFRAME_COUNT;
        struct Keyframe[KEYFRAME_COUNT]
        {
            float VALUE;//radians
            float TIME;//centiseconds
        }:
    };
};

struct TextureDefs //define texture name and id bindings
{
    string[4] ident ="imag";
    uint16 TEX_COUNT;
    struct TexDef[TEX_COUNT]
    {
        uint16 serializer_id;//1029
        uint16 unk;
        uint16 TEX_ID;
        uint16 strLen;
        string[strLen] texName;
    };
};

struct MaterialChunk //defines parameters of materials and shaders
{
    string[4] ident ="mate";
    uint16 MAT_COUNT;

    struct Material[MAT_COUNT]
    {
        uint16 serializer_id;//1024
        uint16 strLen;
        string[strLen] MatName;
        uint32 TYPE;//..maybe hash? looked up in a registry

        //Texture slots

        //ambient
        uint16 aCount;
        for (int i = 0; i < aCount; i++)
        {
            uint16 serializer_id;
            if (serializer_id == 1029)
            {
                uint32 unk;
            }
            else
            {
                uint32 unk2;
            }
        }

        //diffuse
        uint16 dCount;
        for (int i = 0; i < dCount; i++)
        {
            uint16 serializer_id;
            if (serializer_id == 1029)
            {
                uint32 unk;
            }
            else
            {
                uint32 unk2;
            }
        }

        //specular
        uint16 sCount;
        for (int i = 0; i < sCount; i++)
        {
            uint16 serializer_id;
            if (serializer_id == 1029)
            {
                uint32 unk;
            }
            else
            {
                uint32 unk2;
            }
        }

        //possibly parameter slots

        uint16 unk1Count;
        for (int i = 0; i < unk1Count; i++)
        {
            uint16 serializer_id;
            float unk12;
        }

        uint16 unk2Count;
        for (int i = 0; i < unk2Count; i++)
        {
            uint16 serializer_id;
            float unk22;
        }

        byte HAS_TEXTURE;

        if (HAS_TEXTURE == 1)
        {
            uint16 TEX_COUNT;
            struct TexureMap[TEX_COUNT]
            {
                uint16 serializer_id;
                uint32 TEX_ID;
            }  
        }

        uint16 strLen;
        string[strLen] unkNullString;    
    };

    //two possible chunks could follow:

    struct MPSS_Subchunk //clear usage unknown
    {
        string header = "MPSS";
        uint16 count;
        struct MPSS_Entry[count]
        {
            uint16 unk32;
            byte[16] payload;
        }
    }

    struct MPDS_Subchunk //string to value shader parameter chunk
    {
        string header = "MPDS";
        uint16 count;

        struct MPDS_Entry[count]
        {
            uint16 strLen;
            string[strLen] Name;
            byte[32] value;
        }
    }
};

struct LightChunk //defines parameters of lights in a scene
{
    char[4] ident = "ligh";
    int16 LIGHT_COUNT;

    struct light[LIGHT_COUNT]
    {
        uint16 serializer_id;
        uint16 strLen;
        char[strLen] light_name;
        byte[49] unk40; //transform matrix along with color vals
    }

}

struct ModeBuffer//marks the start of a submesh list and its buffers                                 
{
    char[4] ident = "mode";
    uint16 serializer_id;//513
    uint16 strLen;
    char[strLen] unkName; //possibly the root node
    byte[4] unk; 
    uint16 unkC;  
};

struct MeshMeta//a submesh starts with some metadata about its bounding size,name, and its boneMap
{
    uint16 serializer_id;//770 0x0302
    uint16 strLen;
    char[strLen] MESH_NAME; 
    byte[4] unk;  
    uint16 boneMapCount;
    struct HashedBoneMap[boneMapCount]
    {
        uint32 boneHash;//SSFNV1a hashed bone name 
    }
    float unk3;
    byte unk2;
    byte[24] AABB;
}
struct MeshBegin //indicates the beginning of a submesh
{
    string[4] ident ="verb";
};
struct FaceBuffer 
{
    string[4] ident = "surf";
    int16 FACE_COUNT;
    struct Face [FACE_COUNT]//stride: 6 //type: triangle list // winding:clockwise
    {
        uint16 A;
        uint16 B;
        uint16 C;
    };
};

struct VertexBuffer 
{
    string[4] ident = "coor";
    uint16 VERTEX_COUNT;
    struct Vertex [VERTEX_COUNT] //stride 12
    {
        float x;
        float y;
        float z;
    };
};

struct NormalBuffer
{
    string[4] ident ="norm";
    uint16 NORM_COUNT; //should be the same as VERTEX_COUNT
    struct Normal[NORM_COUNT]//stride 12
    {
        float nx;
        float ny;
        float nz;
    };
};

struct BinormalBuffer//binormal buffer (not present in any file)
{
    string[4] ident ="bino";
    uint16 BINO_COUNT; //should be the same as VERTEX_COUNT
    struct BiNormal[NORM_COUNT]//stride 12
    {
        float bx;
        float by;
        float bz;
    };
};

struct UV0Buffer
{
    string[4] ident ="tex0";
    uint16 UV0_COUNT;    //should be the same as VERTEX_COUNT
    struct UV[UV0_COUNT] //stride 8
    {
        float u;
        float v;
    };
};

struct UV1Buffer
{
    string[4] ident ="tex1";
    uint16 UV1_COUNT;    //should be the same as VERTEX_COUNT
    struct UV[UV1_COUNT] //stride 8
    {
        float u;
        float v;
    };
};

struct VertexColors
{
    string[4] ident = "colo";
    uint16 VERTEX_COUNT;   //should be the same as VERTEX_COUNT
    struct UV[UV1_COUNT] //stride 4
    {
        byte r,g,b,a;
    };
}


struct TangentBuffer //signless tangent vector

{
    char[4] ident ="tan ";
    uint16 TANG_COUNT;      //should be the same as VERTEX_COUNT
    struct Tang[TANG_COUNT]//stride 12
    {
        float tx;
        float ty;
        float tz;
    };
};

struct WeightBuffer //Weight values for each bone assigned to a vertex
{
    char[4] ident ="weig";
    uint16 WEIGHT_COUNT;
    struct VertexWeight[WEIGHT_COUNT] //stride 16 
    {
        float w1;
        float w2;
        float w3;
        float w4;
    };
};

struct VBIBuffer //Vertex Bone Index, in order, bone indices that influence a vertex
                 //this table is local to the current vertex buffer
{
    char[4] ident ="bone";
    uint16 VERTEX_COUNT;
    struct VBI[VERTEX_COUNT]
    {
        byte boneIDX1;
        byte boneIDX2;
        byte boneIDX3;
        byte boneIDX4;
    };
};


//
struct Skeleton //Bone Node Tree, defines the bone relationships
{
    char[4] ident ="skel";
    struct BoneName[BONE_COUNT] //Bone count read from POSE chunk
    {
        uint16 serializer_id; //257=root 258=child
        uint16 strLen;
        char[strLen] BONE_NAME;
        uint32 unk2;
        uint16 CHILD_COUNT;
    };
};

struct RestPose //defines the rest pose of the skeleton
{
    char[4] ident ="base";
    uint16 strLen;
    char[strLen] POSE_NAME;
    int16 BONE_COUNT;
    struct BoneTrs[BONE_COUNT]
    {
        uint16 serializer_id;//1537
        uint16 strLen;
        char[strLen] BONE_NAME;
        float sx, sy, sz; //scale
        float rx, ry, rz; //rotation
        float tx, ty, tz; //translation
    };
};



struct MeshEnd //indicates the end of a mesh
{
    string[4] ident ="vere";
    uint16 strLen;
    char[strLen] NAME;
    byte[2] padding;

};

struct EndFlag //indicates the end of the file
{
    string[4] ident ="end "
}
```



## _tex.BIN  (TEXTURE CONTAINER)
```c#
//information is related to the decompressed file
struct Header
{
    uint32 VERSION;
    uint32 FILE_SIZE;
    uint32 tex_ident;
    uint32 unk;
    uint32 TEXTURE_COUNT;
};

struct TextureDecl[TEXTURE_COUNT]
{
    uint32 HASH;//hashed texture name minus the extension
    uint32 OFFSET;//absolute offset
    uint32 SIZE;
};
//follows texture buffers at OFFSET with SIZE
//TGA or DDS
```


## Thanks to
- @REDxEYE for helping to reverse the material buffer


