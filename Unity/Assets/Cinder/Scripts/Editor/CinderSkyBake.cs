using System;
using System.IO;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Cinder.Editor {
 public static class CinderSkyBake {
  [Serializable] sealed class CardinalReceipt {public CubemapCardinals.Sample[] faces;}
  [Serializable] sealed class AmbientSample {public float[] normal,rgb,expected;public float maxError;}
  [Serializable] sealed class AmbientReceipt {
   public int version=1,samples;public string sourceSha256,orientedSha256,coefficientLayout,integration;
   public float environmentIntensity,whiteNormalizer,maxWhiteFurnaceError,hemisphereIntensity,hemisphereLambertDivisor,maxHemisphereError;
   public float[] hemisphereSkyLinear,hemisphereGroundLinear,coefficients,environmentCoefficients,hemisphereCoefficients;
   public bool whiteFurnacePass,hemispherePass;public string nativeSunPolicy="Native EnvSunExtract clamp applied before diffuse SH; see environment-sun.json. Existing scene directional sun prevents analytic reinjection.";public AmbientSample[] whiteFurnace,hemisphereChecks,ambientChecks;
  }
  static string Hash(byte[] data){using(var hash=SHA256.Create())return BitConverter.ToString(hash.ComputeHash(data)).Replace("-","").ToLowerInvariant();}
  static Vector3 SphereDirection(int i,int count){float y=1-2*(i+.5f)/count,r=Mathf.Sqrt(Mathf.Max(0,1-y*y)),angle=i*2.399963229728653f;return new Vector3(Mathf.Cos(angle)*r,y,Mathf.Sin(angle)*r);}
  static Vector3[] EvaluationNormals(){var normals=new Vector3[70];normals[0]=Vector3.right;normals[1]=Vector3.left;normals[2]=Vector3.up;normals[3]=Vector3.down;normals[4]=Vector3.forward;normals[5]=Vector3.back;for(int i=0;i<64;i++)normals[i+6]=SphereDirection(i,64);return normals;}
  static float[] Coefficients(SphericalHarmonicsL2 sh){var values=new float[27];for(int channel=0;channel<3;channel++)for(int coefficient=0;coefficient<9;coefficient++)values[channel*9+coefficient]=sh[channel,coefficient];return values;}
  static bool Finite(float v)=>!float.IsNaN(v)&&!float.IsInfinity(v);
  static float MaxError(Color a,Color b)=>Mathf.Max(Mathf.Abs(a.r-b.r),Mathf.Max(Mathf.Abs(a.g-b.g),Mathf.Abs(a.b-b.b)));
  static AmbientSample[] Samples(SphericalHarmonicsL2 sh,Vector3[] normals,Func<Vector3,Color> expected,out float maximum){
   var colors=new Color[normals.Length];sh.Evaluate(normals,colors);var rows=new AmbientSample[normals.Length];maximum=0;
   for(int i=0;i<normals.Length;i++){if(!Finite(colors[i].r)||!Finite(colors[i].g)||!Finite(colors[i].b))throw new InvalidOperationException("Nonfinite baked ambient SH evaluation");Color target=expected!=null?expected(normals[i]):Color.black;float error=expected!=null?MaxError(colors[i],target):-1;maximum=Mathf.Max(maximum,error);rows[i]=new AmbientSample{normal=new[]{normals[i].x,normals[i].y,normals[i].z},rgb=new[]{colors[i].r,colors[i].g,colors[i].b},expected=expected!=null?new[]{target.r,target.g,target.b}:null,maxError=error};}return rows;
  }
  static void BakeAmbient(Texture2D oriented,byte[] sourceBytes,byte[] orientedBytes){
   const int count=4096;const float environmentIntensity=.65f,hemisphereIntensity=.24f;
   var white=new SphericalHarmonicsL2();var environment=new SphericalHarmonicsL2();
   for(int i=0;i<count;i++){
    Vector3 direction=SphereDirection(i,count);float u=Mathf.Repeat(.5f-Mathf.Atan2(direction.z,direction.x)/(2*Mathf.PI),1),v=1-Mathf.Acos(direction.y)/Mathf.PI;
    Color radiance=oriented.GetPixelBilinear(u,v);if(!Finite(radiance.r)||!Finite(radiance.g)||!Finite(radiance.b))throw new InvalidOperationException("Nonfinite source HDR ambient sample");
    white.AddDirectionalLight(direction,Color.white,1);environment.AddDirectionalLight(direction,radiance,1);
   }
   var normals=EvaluationNormals();var rawWhite=new Color[6];white.Evaluate(new[]{Vector3.right,Vector3.left,Vector3.up,Vector3.down,Vector3.forward,Vector3.back},rawWhite);
   float whiteMean=0;foreach(var sample in rawWhite)whiteMean+=(sample.r+sample.g+sample.b)/18;
   if(!Finite(whiteMean)||whiteMean<=0)throw new InvalidOperationException("Invalid Unity white-furnace SH normalization");
   float normalization=1/whiteMean;white=white*normalization;environment=environment*(normalization*environmentIntensity);
   var whiteChecks=Samples(white,normals,_=>Color.white,out float whiteError);if(whiteError>.002f)throw new InvalidOperationException("Baked ambient white furnace exceeded .002: "+whiteError);
   // Native HemisphereLight is already a normal-dependent irradiance blend.
   // Represent it as constant + Y-linear SH directly, rather than applying a
   // second Lambert convolution to a hemisphere radiance function.
   Color sky=new Color(189/255f,212/255f,237/255f,1).linear*(hemisphereIntensity/Mathf.PI);
   Color ground=new Color(106/255f,96/255f,78/255f,1).linear*(hemisphereIntensity/Mathf.PI);
   var ambientBasis=new SphericalHarmonicsL2();ambientBasis.AddAmbientLight(Color.white);var ambientValues=new Color[1];ambientBasis.Evaluate(new[]{Vector3.up},ambientValues);
   var up=new SphericalHarmonicsL2();up.AddDirectionalLight(Vector3.up,Color.white,1);var down=new SphericalHarmonicsL2();down.AddDirectionalLight(Vector3.down,Color.white,1);
   var yBasis=up+down*(-1);var axisValues=new Color[1];yBasis.Evaluate(new[]{Vector3.up},axisValues);
   var hemisphere=new SphericalHarmonicsL2();
   for(int channel=0;channel<3;channel++){
    float constantUnit=ambientValues[0][channel],linearUnit=axisValues[0][channel];if(!Finite(constantUnit)||!Finite(linearUnit)||Mathf.Abs(constantUnit)<1e-8f||Mathf.Abs(linearUnit)<1e-8f)throw new InvalidOperationException("Unity hemisphere SH calibration failed");
    float mean=(sky[channel]+ground[channel])*.5f,delta=(sky[channel]-ground[channel])*.5f;
    for(int coefficient=0;coefficient<9;coefficient++)hemisphere[channel,coefficient]=ambientBasis[channel,coefficient]*(mean/constantUnit)+yBasis[channel,coefficient]*(delta/linearUnit);
   }
   var hemisphereChecks=Samples(hemisphere,normals,n=>Color.LerpUnclamped(ground,sky,.5f*n.y+.5f),out float hemiError);if(hemiError>.0002f)throw new InvalidOperationException("Baked native hemisphere SH exceeded .0002: "+hemiError);
   var combined=environment+hemisphere;var ambientChecks=Samples(combined,normals,null,out _);var coefficients=Coefficients(combined);foreach(float value in coefficients)if(!Finite(value))throw new InvalidOperationException("Nonfinite baked ambient SH coefficient");
   var receipt=new AmbientReceipt{samples=count,sourceSha256=Hash(sourceBytes),orientedSha256=Hash(orientedBytes),coefficientLayout="channel-major: index=channel*9+coefficient; channel RGB, coefficient Unity SphericalHarmonicsL2 order",integration="Uniform Fibonacci sphere + Unity AddDirectionalLight, calibrated by unit constant-radiance white furnace to outgoing Lambert mean E/pi=1. HDR environment*0.65 plus exact native HemisphereLight normal blend from linear hex colours*0.24/pi. L2 is a low-frequency approximation to native diffuse PMREM, not per-pixel parity.",environmentIntensity=environmentIntensity,whiteNormalizer=normalization,maxWhiteFurnaceError=whiteError,hemisphereIntensity=hemisphereIntensity,hemisphereLambertDivisor=Mathf.PI,maxHemisphereError=hemiError,hemisphereSkyLinear=new[]{sky.r,sky.g,sky.b},hemisphereGroundLinear=new[]{ground.r,ground.g,ground.b},coefficients=coefficients,environmentCoefficients=Coefficients(environment),hemisphereCoefficients=Coefficients(hemisphere),whiteFurnacePass=true,hemispherePass=true,whiteFurnace=whiteChecks,hemisphereChecks=hemisphereChecks,ambientChecks=ambientChecks};
   File.WriteAllText("Assets/Resources/Cinder/ambient-sh.json",JsonUtility.ToJson(receipt,true));Debug.Log("AMBIENT SH CPU BAKE samples="+count+" whiteFurnaceMax="+whiteError+" nativeHemisphereMax="+hemiError);
  }
  static Texture2D Orient(Texture2D source){
   var pixels=new Color[source.width*source.height];const float rotation=3.4095478f/(2*Mathf.PI);
   source.wrapModeU=TextureWrapMode.Repeat;source.wrapModeV=TextureWrapMode.Clamp;
   for(int y=0;y<source.height;y++)for(int x=0;x<source.width;x++)pixels[y*source.width+x]=source.GetPixelBilinear(Mathf.Repeat(1-(x+.5f)/source.width+rotation,1),(y+.5f)/source.height);
   var result=new Texture2D(source.width,source.height,TextureFormat.RGBAFloat,false,true);result.wrapModeU=TextureWrapMode.Repeat;result.wrapModeV=TextureWrapMode.Clamp;result.SetPixels(pixels);result.Apply();return result;
  }
  static Cubemap ImportCube(string path,bool convolve){
   AssetDatabase.ImportAsset(path);var importer=(TextureImporter)AssetImporter.GetAtPath(path);importer.textureShape=TextureImporterShape.TextureCube;
   importer.generateCubemap=TextureImporterGenerateCubemap.Cylindrical;importer.maxTextureSize=128;importer.sRGBTexture=false;importer.isReadable=true;
   importer.mipmapEnabled=true;importer.filterMode=FilterMode.Trilinear;importer.textureCompression=TextureImporterCompression.Uncompressed;
   var settings=new TextureImporterSettings();importer.ReadTextureSettings(settings);settings.cubemapConvolution=convolve?TextureImporterCubemapConvolution.Specular:TextureImporterCubemapConvolution.None;importer.SetTextureSettings(settings);importer.SaveAndReimport();
   return AssetDatabase.LoadAssetAtPath<Cubemap>(path)??throw new InvalidOperationException("Cannot import environment cube "+path);
  }
  static Cubemap NativeReflection(Cubemap original,Cubemap filtered){
   if(original.width!=filtered.width||original.mipmapCount!=filtered.mipmapCount)throw new InvalidOperationException("Native environment cube mip layouts differ");
   var result=new Cubemap(original.width,TextureFormat.RGBAHalf,true){name="Native sky mip0 and sun-clamped filtered rough mips",filterMode=FilterMode.Trilinear,wrapMode=TextureWrapMode.Clamp};
   foreach(CubemapFace face in new[]{CubemapFace.PositiveX,CubemapFace.NegativeX,CubemapFace.PositiveY,CubemapFace.NegativeY,CubemapFace.PositiveZ,CubemapFace.NegativeZ})
    for(int mip=0;mip<original.mipmapCount;mip++)result.SetPixels((mip==0?original:filtered).GetPixels(face,mip),face,mip);
   result.Apply(false,false);
   const string asset="Assets/Resources/Cinder/sky-reflection-native.asset";var existing=AssetDatabase.LoadAssetAtPath<Cubemap>(asset);
   if(existing){EditorUtility.CopySerialized(result,existing);EditorUtility.SetDirty(existing);UnityEngine.Object.DestroyImmediate(result);result=existing;}else AssetDatabase.CreateAsset(result,asset);
   AssetDatabase.SaveAssets();return result;
  }
  public static void Run() {
   const string source="Assets/Resources/Cinder/sky.hdr",oriented="Assets/Resources/Cinder/sky-oriented.exr";
   const string cube="Assets/Resources/Cinder/sky-reflection-filtered.exr",rawCube="Assets/Cinder/Art/Generated/sky-reflection-original.exr";
   const string clampedPath="Assets/Resources/Cinder/sky-reflection-sun-clamped.exr";
   var importer=(TextureImporter)AssetImporter.GetAtPath(source);importer.textureType=TextureImporterType.Default;importer.textureShape=TextureImporterShape.Texture2D;
   importer.sRGBTexture=false;importer.isReadable=true;importer.maxTextureSize=1024;importer.textureCompression=TextureImporterCompression.Uncompressed;importer.SaveAndReimport();
   var panorama=AssetDatabase.LoadAssetAtPath<Texture2D>(source);byte[] sourceBytes=File.ReadAllBytes(source);
   string root=Path.GetFullPath(Path.Combine(Application.dataPath,"../.."));var nativeSources=NativeEnvironmentSun.ValidateNativeSources(root);
   Color[] nativePixels=panorama.GetPixels();var rgba=new float[nativePixels.Length*4];for(int i=0;i<nativePixels.Length;i++){rgba[i*4]=nativePixels[i].r;rgba[i*4+1]=nativePixels[i].g;rgba[i*4+2]=nativePixels[i].b;rgba[i*4+3]=nativePixels[i].a;}
   var extraction=NativeEnvironmentSun.Extract(panorama.width,panorama.height,rgba);
   var receipt=extraction.receipt;receipt.sourceSha256=Hash(sourceBytes);receipt.nativeSources=nativeSources;receipt.nativeSourcesMatch=true;
   Vector3 direction=Quaternion.AngleAxis(3.4095478f*Mathf.Rad2Deg,Vector3.up)*new Vector3(receipt.directionNative[0],receipt.directionNative[1],receipt.directionNative[2]);receipt.directionWorld=new[]{direction.x,direction.y,direction.z};
   if(extraction.clamped!=null)for(int i=0;i<nativePixels.Length;i++)nativePixels[i]=new Color(extraction.clamped[i*4],extraction.clamped[i*4+1],extraction.clamped[i*4+2],extraction.clamped[i*4+3]);
   var clampedNative=new Texture2D(panorama.width,panorama.height,TextureFormat.RGBAFloat,false,true);clampedNative.SetPixels(nativePixels);clampedNative.Apply();
   Texture2D image=null,clamped=null;
   try{
    // Visible sky retains the original sun. Only diffuse and rough reflection
    // levels consume the native sun-clamped copy; level0 remains a true mirror.
    image=Orient(panorama);clamped=Orient(clampedNative);byte[] visibleData=image.EncodeToEXR(Texture2D.EXRFlags.CompressZIP),clampedData=clamped.EncodeToEXR(Texture2D.EXRFlags.CompressZIP);
    File.WriteAllBytes(oriented,visibleData);File.WriteAllBytes(clampedPath,clampedData);receipt.clampedSourceSha256=Hash(clampedData);File.WriteAllText("Assets/Resources/Cinder/environment-sun.json",JsonUtility.ToJson(receipt,true));
    var originalSource=CubemapCardinals.PrepareForCylindricalImport(image);var filteredSource=CubemapCardinals.PrepareForCylindricalImport(clamped);
    try{Directory.CreateDirectory(Path.GetDirectoryName(rawCube));File.WriteAllBytes(rawCube,originalSource.EncodeToEXR(Texture2D.EXRFlags.CompressZIP));File.WriteAllBytes(cube,filteredSource.EncodeToEXR(Texture2D.EXRFlags.CompressZIP));}
    finally{UnityEngine.Object.DestroyImmediate(originalSource);UnityEngine.Object.DestroyImmediate(filteredSource);}
    AssetDatabase.ImportAsset(oriented);AssetDatabase.ImportAsset(clampedPath);
    var sky=(TextureImporter)AssetImporter.GetAtPath(oriented);sky.sRGBTexture=false;sky.maxTextureSize=1024;sky.mipmapEnabled=false;sky.filterMode=FilterMode.Bilinear;sky.textureCompression=TextureImporterCompression.Uncompressed;sky.SaveAndReimport();
    var reflection=NativeReflection(ImportCube(rawCube,false),ImportCube(cube,true));
    BakeAmbient(clamped,sourceBytes,clampedData);var cardinals=CubemapCardinals.Read(image,reflection);File.WriteAllText("Assets/Resources/Cinder/sky-cardinals.json",JsonUtility.ToJson(new CardinalReceipt{faces=cardinals},true));
    File.WriteAllText("Assets/Resources/Cinder/sky-bake.json","{\"sourceSha256\":\""+Hash(sourceBytes)+"\",\"nativeRotationRadians\":3.4095478,\"longitudeConventionConverted\":true,\"reflectionSize\":128,\"convolution\":\"Specular on native sun-clamped source\",\"runtimeRotationDegrees\":0,\"cubeImporterLongitudeOffsetDegrees\":-90,\"runtimeReflectionAsset\":\"Cinder/sky-reflection-native\",\"mip0\":\"Original HDR\",\"mips1Plus\":\"Native sun-clamped HDR\"}");
    Debug.Log("NATIVE ENV SUN found="+receipt.found+" peak="+receipt.peakLuminance+" mean="+receipt.meanLuminance+" disc="+receipt.discTexels+" haloCapped="+receipt.cappedTexels);
   }finally{if(image)UnityEngine.Object.DestroyImmediate(image);if(clamped)UnityEngine.Object.DestroyImmediate(clamped);UnityEngine.Object.DestroyImmediate(clampedNative);}
  }
 }
}
