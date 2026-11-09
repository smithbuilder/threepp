using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using UnityEngine.Rendering;

namespace Cinder.Editor
{
    // Offline glTF 2.0 importer for this repo's uncompressed, rigid authored kits.
    // Fail closed on skins, sparse/compressed geometry and unsupported modes.
    public static class GlbImport
    {
        [Serializable] class Doc { public Node[] nodes;public GMesh[] meshes;public Accessor[] accessors;public BufferView[] bufferViews;public GMat[] materials;public GImage[] images;public GTexture[] textures;public object[] skins; }
        [Serializable] class Node {public string name;public int mesh=-1;public int[] children;public float[] translation,rotation,scale,matrix;}
        [Serializable] class GMesh {public string name;public Prim[] primitives;}
        [Serializable] class Prim {public Attr attributes;public int indices=-1,material=-1;public int mode=4;}
        [Serializable] class Attr {public int POSITION=-1,NORMAL=-1,TEXCOORD_0=-1,COLOR_0=-1,TANGENT=-1;}
        [Serializable] class Accessor {public int bufferView=-1,byteOffset,componentType,count;public string type;public bool normalized;}
        [Serializable] class BufferView {public int buffer,byteOffset,byteLength,byteStride;}
        [Serializable] class GMat {public string name,alphaMode;public Pbr pbrMetallicRoughness;public Tex normalTexture;public float alphaCutoff=.5f;public bool doubleSided;public float[] emissiveFactor;public Extensions extensions;}
        [Serializable] class Extensions {public Coat KHR_materials_clearcoat;}
        [Serializable] class Coat {public float clearcoatFactor,clearcoatRoughnessFactor;}
        [Serializable] class Pbr {public float[] baseColorFactor;public Tex baseColorTexture,metallicRoughnessTexture;public float metallicFactor=1,roughnessFactor=1;}
        [Serializable] class Tex {public int index=-1;public float scale=1;}
        [Serializable] class GImage {public int bufferView=-1;public string uri,mimeType;}
        [Serializable] class GTexture {public int source;}
        static float[] Values(Doc d,byte[] bin,int index)
        {
            if(index<0)return null;var a=d.accessors[index];if(a.bufferView<0)throw new Exception("Sparse/empty accessor unsupported");var v=d.bufferViews[a.bufferView];if(v.buffer!=0)throw new Exception("External geometry buffer unsupported");
            int n=a.type=="SCALAR"?1:a.type=="VEC2"?2:a.type=="VEC3"?3:4,size=a.componentType==5126||a.componentType==5125?4:a.componentType==5123||a.componentType==5122?2:1;
            var r=new float[a.count*n];for(int i=0;i<a.count;i++)for(int k=0;k<n;k++){int p=v.byteOffset+a.byteOffset+i*(v.byteStride>0?v.byteStride:n*size)+k*size;double x;
                switch(a.componentType){case 5126:x=BitConverter.ToSingle(bin,p);break;case 5125:x=BitConverter.ToUInt32(bin,p);break;case 5123:x=BitConverter.ToUInt16(bin,p);if(a.normalized)x/=65535;break;case 5122:x=BitConverter.ToInt16(bin,p);if(a.normalized)x=Math.Max(-1,x/32767);break;case 5121:x=bin[p];if(a.normalized)x/=255;break;case 5120:x=(sbyte)bin[p];if(a.normalized)x=Math.Max(-1,x/127);break;default:throw new Exception("Unsupported accessor component");}r[i*n+k]=(float)x;}
            return r;
        }
        static Vector3[] V3(float[] a){if(a==null)return null;var r=new Vector3[a.Length/3];for(int i=0;i<r.Length;i++)r[i]=new Vector3(a[i*3],a[i*3+1],a[i*3+2]);return r;}
        public static void RefreshCoat(string source,string id){byte[] raw=File.ReadAllBytes(source);var d=JsonUtility.FromJson<Doc>(System.Text.Encoding.UTF8.GetString(raw,20,BitConverter.ToInt32(raw,12)));for(int i=0;i<(d.materials?.Length??0);i++){var mat=AssetDatabase.LoadAssetAtPath<Material>("Assets/Resources/Cinder/Generated/"+id+"/material-"+i+".mat");if(!mat||!mat.HasProperty("_Clearcoat"))continue;var coat=d.materials[i].extensions?.KHR_materials_clearcoat;mat.SetFloat("_Clearcoat",coat?.clearcoatFactor??0);mat.SetFloat("_CoatRoughness",coat?.clearcoatRoughnessFactor??.06f);EditorUtility.SetDirty(mat);}}
        public static void Import(string source,string id)
        {
            string dir="Assets/Resources/Cinder/Generated/"+id;Directory.CreateDirectory(dir);
            byte[] raw=File.ReadAllBytes(source);if(BitConverter.ToUInt32(raw,0)!=0x46546c67||BitConverter.ToUInt32(raw,4)!=2)throw new Exception("glTF 2 binary required");
            int jlen=BitConverter.ToInt32(raw,12);string json=System.Text.Encoding.UTF8.GetString(raw,20,jlen);if(json.Contains("\"sparse\"")||json.Contains("KHR_draco_mesh_compression")||json.Contains("\"skins\""))throw new Exception("Unsupported compressed/skinned asset");
            var d=JsonUtility.FromJson<Doc>(json);int bstart=20+jlen+8;byte[] bin=raw.Skip(bstart).ToArray();var images=new Dictionary<int,Texture2D>();
            Func<Tex,Texture2D> image=reference=>{
                if(reference==null||reference.index<0||d.textures==null||reference.index>=d.textures.Length)return null;int n=d.textures[reference.index].source;if(images.TryGetValue(n,out var exists))return exists;var im=d.images[n];byte[] bytes;
                if(im.bufferView>=0){var v=d.bufferViews[im.bufferView];bytes=bin.Skip(v.byteOffset).Take(v.byteLength).ToArray();}
                else if(im.uri.StartsWith("data:"))bytes=Convert.FromBase64String(im.uri.Substring(im.uri.IndexOf(',')+1));else bytes=File.ReadAllBytes(Path.Combine(Path.GetDirectoryName(source),im.uri));
                string path=dir+"/image-"+n+".png";var tex=new Texture2D(2,2);if(!tex.LoadImage(bytes))throw new Exception("Texture decode failed");File.WriteAllBytes(path,tex.EncodeToPNG());UnityEngine.Object.DestroyImmediate(tex);AssetDatabase.ImportAsset(path);var ti=(TextureImporter)AssetImporter.GetAtPath(path);ti.maxTextureSize=1024;ti.textureCompression=TextureImporterCompression.Compressed;ti.SaveAndReimport();var result=AssetDatabase.LoadAssetAtPath<Texture2D>(path);images[n]=result;return result;};
            var mats=new List<Material>();foreach(var gm in d.materials??Array.Empty<GMat>()){
                var p=gm.pbrMetallicRoughness??new Pbr();var mat=new Material(Shader.Find(gm.alphaMode=="BLEND"?"Cinder/Glass":"Cinder/Body")){name=gm.name};
                var c=p.baseColorFactor;mat.color=c!=null?new Color(c[0],c[1],c[2],c[3]).gamma:Color.white;mat.mainTexture=image(p.baseColorTexture);mat.SetFloat("_Metallic",p.metallicFactor);mat.SetFloat("_Glossiness",1-p.roughnessFactor);
                if(gm.alphaMode=="BLEND"){mat.SetFloat("_Mode",2);mat.SetOverrideTag("RenderType","Transparent");mat.SetInt("_SrcBlend",(int)BlendMode.SrcAlpha);mat.SetInt("_DstBlend",(int)BlendMode.OneMinusSrcAlpha);mat.SetInt("_ZWrite",0);mat.DisableKeyword("_ALPHAPREMULTIPLY_ON");mat.EnableKeyword("_ALPHABLEND_ON");mat.renderQueue=3000;}
                else if(gm.alphaMode=="MASK"){mat.SetFloat("_Cutoff",gm.alphaCutoff);mat.EnableKeyword("CINDER_CUTOUT");mat.renderQueue=2450;}
                if(mat.HasProperty("_Cull"))mat.SetInt("_Cull",gm.doubleSided?0:2);
                if(gm.emissiveFactor!=null){var e=gm.emissiveFactor;mat.SetColor("_EmissionColor",new Color(e[0],e[1],e[2]));mat.EnableKeyword("_EMISSION");}
                var normal=image(gm.normalTexture);if(normal){var ni=(TextureImporter)AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(normal));ni.textureType=TextureImporterType.NormalMap;ni.SaveAndReimport();mat.SetTexture("_BumpMap",normal);mat.SetFloat("_BumpScale",gm.normalTexture.scale);mat.EnableKeyword("_NORMALMAP");}
                // glTF green=roughness, blue=metal. Unity red=metal, alpha=smoothness.
                var mr=image(p.metallicRoughnessTexture);if(mr){var mi=(TextureImporter)AssetImporter.GetAtPath(AssetDatabase.GetAssetPath(mr));mi.isReadable=true;mi.sRGBTexture=false;mi.SaveAndReimport();var px=mr.GetPixels();for(int k=0;k<px.Length;k++)px[k]=new Color(px[k].b*p.metallicFactor,0,0,1-px[k].g*p.roughnessFactor);var packed=new Texture2D(mr.width,mr.height,TextureFormat.RGBA32,true,true);packed.SetPixels(px);packed.Apply();string mp=dir+"/packed-"+mats.Count+".png";File.WriteAllBytes(mp,packed.EncodeToPNG());UnityEngine.Object.DestroyImmediate(packed);AssetDatabase.ImportAsset(mp);var mpi=(TextureImporter)AssetImporter.GetAtPath(mp);mpi.sRGBTexture=false;mpi.SaveAndReimport();mat.SetTexture("_MetallicGlossMap",AssetDatabase.LoadAssetAtPath<Texture2D>(mp));mat.EnableKeyword("_METALLICGLOSSMAP");}
                AssetDatabase.CreateAsset(mat,dir+"/material-"+mats.Count+".mat");mat.name=gm.name;EditorUtility.SetDirty(mat);mats.Add(mat);
            }
            var fallback=new Material(Shader.Find("Cinder/Body"));var meshGroups=new List<(Mesh,Material)>[d.meshes.Length];long triangles=0;
            for(int i=0;i<d.meshes.Length;i++){meshGroups[i]=new List<(Mesh,Material)>();int part=0;foreach(var p in d.meshes[i].primitives){if(p.mode!=4)throw new Exception("Only triangle lists supported");var m=new Mesh{name=d.meshes[i].name??"part",indexFormat=IndexFormat.UInt32};m.vertices=V3(Values(d,bin,p.attributes.POSITION));var normals=V3(Values(d,bin,p.attributes.NORMAL));if(normals!=null)m.normals=normals;
                var uv=Values(d,bin,p.attributes.TEXCOORD_0);if(uv!=null){var u=new Vector2[uv.Length/2];for(int k=0;k<u.Length;k++)u[k]=new Vector2(uv[k*2],1-uv[k*2+1]);m.uv=u;}
                var colors=Values(d,bin,p.attributes.COLOR_0);if(colors!=null){int n=d.accessors[p.attributes.COLOR_0].type=="VEC3"?3:4;var c=new Color[colors.Length/n];for(int k=0;k<c.Length;k++)c[k]=new Color(colors[k*n],colors[k*n+1],colors[k*n+2],n==4?colors[k*n+3]:1);m.colors=c;}
                int[] indices=p.indices>=0?Values(d,bin,p.indices).Select(x=>(int)x).ToArray():Enumerable.Range(0,m.vertexCount).ToArray();// The donor and Unity share numeric +Y-up/+Z-forward coordinates. Preserve
                // winding with that identity basis; flipping only indices turns solids inside out.
                m.triangles=indices;if(normals==null)m.RecalculateNormals();m.RecalculateBounds();if(uv!=null)m.RecalculateTangents();triangles+=indices.Length/3;AssetDatabase.CreateAsset(m,dir+"/mesh-"+i+"-"+(part++)+".asset");m.name=d.meshes[i].name??"part";EditorUtility.SetDirty(m);meshGroups[i].Add((m,p.material>=0?mats[p.material]:fallback));
            }}
            var root=new GameObject(id);var nodes=d.nodes.Select((n,i)=>new GameObject(string.IsNullOrEmpty(n.name)?"node-"+i:n.name)).ToArray();
            for(int i=0;i<nodes.Length;i++){var n=d.nodes[i];var t=nodes[i].transform;t.SetParent(root.transform,false);if(n.translation!=null)t.localPosition=new Vector3(n.translation[0],n.translation[1],n.translation[2]);if(n.rotation!=null)t.localRotation=new Quaternion(n.rotation[0],n.rotation[1],n.rotation[2],n.rotation[3]);if(n.scale!=null)t.localScale=new Vector3(n.scale[0],n.scale[1],n.scale[2]);if(n.matrix!=null){var a=new Matrix4x4();for(int k=0;k<16;k++)a[k]=n.matrix[k];t.localPosition=a.GetColumn(3);t.localRotation=a.rotation;t.localScale=a.lossyScale;}
                if(n.mesh>=0)foreach(var item in meshGroups[n.mesh]){var g=new GameObject(item.Item1.name??"mesh");g.transform.SetParent(t,false);g.AddComponent<MeshFilter>().sharedMesh=item.Item1;var renderer=g.AddComponent<MeshRenderer>();renderer.sharedMaterial=item.Item2;renderer.shadowCastingMode=item.Item2.renderQueue>=3000?ShadowCastingMode.Off:ShadowCastingMode.On;}
            }
            for(int i=0;i<nodes.Length;i++)foreach(int child in d.nodes[i].children??Array.Empty<int>())nodes[child].transform.SetParent(nodes[i].transform,false);
            PrefabUtility.SaveAsPrefabAsset(root,dir+"/"+id+".prefab");UnityEngine.Object.DestroyImmediate(root);Debug.Log("IMPORTED "+id+" triangles="+triangles+" nodes="+nodes.Length+" materials="+mats.Count);
        }
    }
}
