using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;

namespace Cinder.Editor
{
    // Applies the original CityBlock material contract to the frozen, offline city
    // export. Geometry, UV density and baked vertex shading are supplied by the GLB.
    public static class NativeCityMaterials
    {
        [Serializable] sealed class MaterialSet { public NativeMaterial[] materials; }
        [Serializable] sealed class NativeMaterial
        {
            public string id,name;
            public float[] color,normalScale,emissive;
            public float roughness=1,metalness,alphaCutoff;
            public bool doubleSided;
            public Maps maps;
        }
        [Serializable] sealed class Maps { public string color,normal,roughness; }
        [Serializable] sealed class Receipt
        {
            public string source,sourceSha256;
            public MaterialReceipt[] materials;
        }
        [Serializable] sealed class MaterialReceipt
        {
            public string id,name,shader,colorMap,normalMap,roughnessMap,colorWrapMode;
            public float roughness,metalness,normalScale,alphaCutoff;
            public bool doubleSided;
        }
        const string Generated="Assets/Resources/Cinder/Generated/mercer-city";
        static string Hash(byte[] bytes)
        {
            using(var hash=SHA256.Create())return BitConverter.ToString(hash.ComputeHash(bytes)).Replace("-","").ToLowerInvariant();
        }
        static void WriteChanged(string path,byte[] bytes)
        {
            if(File.Exists(path)&&File.ReadAllBytes(path).SequenceEqual(bytes))return;
            File.WriteAllBytes(path,bytes);
        }
        static Color AuthoredColor(float[] channels,string description)
        {
            if(channels==null||channels.Length<3||channels.Any(v=>float.IsNaN(v)||float.IsInfinity(v)||v<0))
                throw new Exception("Invalid native city "+description);
            // Native colours are linear; Unity colour properties use the same gamma
            // representation as the other imported glTF base-colour properties.
            return new Color(channels[0],channels[1],channels[2],channels.Length>3?channels[3]:1).gamma;
        }
        static Texture2D Texture(string repositoryRoot,string source,string role,TextureWrapMode wrap=TextureWrapMode.Repeat)
        {
            if(string.IsNullOrEmpty(source))return null;
            string root=Path.GetFullPath(Path.Combine(repositoryRoot,"Unity"))+Path.DirectorySeparatorChar;
            string absolute=Path.GetFullPath(Path.Combine(root,source));
            if(!source.StartsWith("Assets/",StringComparison.Ordinal)||!absolute.StartsWith(root,StringComparison.OrdinalIgnoreCase)||!File.Exists(absolute))
                throw new Exception("Missing or invalid native city material map: "+source);
            // Keep the copied source immutable and make distinct role imports. A shared
            // image may otherwise be mutated from colour to normal/data by a later bind.
            byte[] bytes=File.ReadAllBytes(absolute);
            string directory=Generated+"/native-textures";Directory.CreateDirectory(directory);
            string path=directory+"/"+Path.GetFileNameWithoutExtension(source)+"-"+Hash(bytes).Substring(0,12)+"-"+role+Path.GetExtension(source);
            WriteChanged(path,bytes);AssetDatabase.ImportAsset(path);
            var importer=AssetImporter.GetAtPath(path) as TextureImporter;
            if(importer==null)throw new Exception("Cannot import native city texture "+source);
            importer.textureType=role=="normal"?TextureImporterType.NormalMap:TextureImporterType.Default;
            importer.sRGBTexture=role=="color";importer.maxTextureSize=1024;
            importer.mipmapEnabled=true;importer.filterMode=FilterMode.Trilinear;importer.anisoLevel=4;
            importer.wrapModeU=wrap;importer.wrapModeV=wrap;
            importer.textureCompression=role=="roughness"?TextureImporterCompression.Uncompressed:TextureImporterCompression.CompressedHQ;
            importer.alphaSource=TextureImporterAlphaSource.FromInput;
            importer.alphaIsTransparency=role=="color";
            importer.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path)??throw new Exception("Native city texture missing after import: "+source);
        }
        public static void Configure(string repositoryRoot)
        {
            string source=Path.Combine(repositoryRoot,"assets/unity/city/materials.json");
            if(!File.Exists(source))throw new Exception("Frozen native city material metadata missing: "+source);
            byte[] sourceBytes=File.ReadAllBytes(source);
            var set=JsonUtility.FromJson<MaterialSet>(System.Text.Encoding.UTF8.GetString(sourceBytes));
            if(set?.materials==null||set.materials.Length==0)throw new Exception("Native city material set is empty");
            var definitions=new Dictionary<string,NativeMaterial>(StringComparer.Ordinal);
            foreach(var definition in set.materials)
            {
                string name=string.IsNullOrEmpty(definition.name)?"city."+definition.id:definition.name;
                if(!definitions.TryAdd(name,definition))throw new Exception("Duplicate native city material: "+name);
            }
            if(!Directory.Exists(Generated))throw new Exception("Import mercer-city before configuring its materials");
            var seen=new HashSet<string>(StringComparer.Ordinal);var receipts=new List<MaterialReceipt>();
            foreach(string path in Directory.GetFiles(Generated,"material-*.mat"))
            {
                var material=AssetDatabase.LoadAssetAtPath<Material>(path);
                if(!material||!definitions.TryGetValue(material.name,out var definition))
                    throw new Exception("Unmapped native city material: "+path+" / "+(material?material.name:"missing"));
                if(!seen.Add(material.name))throw new Exception("Duplicated imported city material: "+material.name);
                string shaderName=definition.id=="leaf"?"Cinder/CityFoliage":"Cinder/City";
                var shader=Shader.Find(shaderName);if(!shader)throw new Exception("Native city shader missing: "+shaderName);
                material.shader=shader;material.color=AuthoredColor(definition.color,material.name+" colour");
                if(definition.roughness<0||definition.roughness>1||definition.metalness<0||definition.metalness>1)
                    throw new Exception("Invalid native city roughness/metalness: "+material.name);
                material.SetFloat("_Roughness",definition.roughness);material.SetFloat("_Metallic",definition.metalness);
                material.SetFloat("_Glossiness",1-definition.roughness);
                var colorWrap=definition.id=="leaf"?TextureWrapMode.Clamp:TextureWrapMode.Repeat;
                material.SetTexture("_MainTex",Texture(repositoryRoot,definition.maps?.color,"color",colorWrap));
                var normal=Texture(repositoryRoot,definition.maps?.normal,"normal");material.SetTexture("_BumpMap",normal);
                float normalScale=definition.normalScale!=null&&definition.normalScale.Length>0?definition.normalScale[0]:1;
                if(definition.normalScale!=null&&definition.normalScale.Length>1&&Mathf.Abs(normalScale-definition.normalScale[1])>1e-6f)
                    throw new Exception("Unequal native city normal axes require explicit shader support: "+material.name);
                material.SetFloat("_BumpScale",normalScale);
                if(normal)material.EnableKeyword("_NORMALMAP");else material.DisableKeyword("_NORMALMAP");
                var roughness=Texture(repositoryRoot,definition.maps?.roughness,"roughness");material.SetTexture("_RoughnessMap",roughness);
                material.SetFloat("_HasRoughnessMap",roughness?1:0);
                material.SetFloat("_Cutoff",definition.alphaCutoff);material.SetInt("_Cull",definition.doubleSided?0:2);
                if(definition.alphaCutoff>0){material.EnableKeyword("CINDER_CUTOUT");material.SetOverrideTag("RenderType","TransparentCutout");material.renderQueue=2450;}
                else{material.DisableKeyword("CINDER_CUTOUT");material.SetOverrideTag("RenderType","Opaque");material.renderQueue=2000;}
                var emission=definition.emissive;
                material.SetColor("_EmissionColor",emission!=null?AuthoredColor(emission,material.name+" emission"):Color.black);
                material.mainTextureScale=definition.id=="sign"?new Vector2(-1,1):Vector2.one;material.mainTextureOffset=definition.id=="sign"?new Vector2(1,0):Vector2.zero;
                material.enableInstancing=true;EditorUtility.SetDirty(material);
                receipts.Add(new MaterialReceipt{id=definition.id,name=material.name,shader=shaderName,roughness=definition.roughness,metalness=definition.metalness,normalScale=normalScale,alphaCutoff=definition.alphaCutoff,doubleSided=definition.doubleSided,colorMap=definition.maps?.color,normalMap=definition.maps?.normal,roughnessMap=definition.maps?.roughness,colorWrapMode=string.IsNullOrEmpty(definition.maps?.color)?"none":colorWrap.ToString()});
            }
            var missing=definitions.Keys.Where(name=>!seen.Contains(name)).ToArray();
            if(missing.Length>0)throw new Exception("Native city definitions not found in GLB: "+string.Join(", ",missing));
            WriteChanged(Generated+"/native-material-receipt.json",System.Text.Encoding.UTF8.GetBytes(JsonUtility.ToJson(new Receipt{source="assets/unity/city/materials.json",sourceSha256=Hash(sourceBytes),materials=receipts.OrderBy(r=>r.name,StringComparer.Ordinal).ToArray()},true)));
            AssetDatabase.Refresh();AssetDatabase.SaveAssets();
            Debug.Log("NATIVE CITY MATERIALS "+receipts.Count+" exact definitions, source SHA256 "+Hash(sourceBytes));
        }
    }
}
