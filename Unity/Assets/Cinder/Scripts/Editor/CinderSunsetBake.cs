using System;
using System.IO;
using System.Security.Cryptography;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Cinder.Editor
{
    // Original authored evening profile derived from the licensed daylight HDR's
    // cloud structure. All generation is offline; the native daylight is intact.
    public static class CinderSunsetBake
    {
        public static readonly Vector3 SunDirectionLinear=new Vector3(.70f,.20f,-.685f).normalized;
        public static readonly Color SunColourLinear=new Color(1,.62f,.35f,1);
        public const float SunIrradiance=2.4f;
        public static float UnitySunIntensity=>SunIrradiance/Mathf.PI;
        public const float EnvironmentIntensity=.65f;
        static readonly Color CityBounceLinear=new Color(.075f,.11f,.16f,1);
        const float SkyRadianceScale=1.8f,DiscRadiusDegrees=.35f,DiscEdgeDegrees=.20f;
        const int AmbientSamples=4096,ReflectionSize=128;
        const string Resource="Assets/Resources/Cinder/",Scratch="Assets/Cinder/Art/Generated/";
        static readonly Color Zenith=new Color(.25f,.37f,.62f,1).linear;
        static readonly Color Lavender=new Color(.42f,.46f,.72f,1).linear;
        static readonly Color Rose=new Color(.84f,.43f,.57f,1).linear;
        static readonly Color Peach=new Color(1,.67f,.43f,1).linear;
        static readonly Color Ground=new Color(.25f,.22f,.24f,1).linear;
        [Serializable] sealed class Recipe
        {
            public int version=1,width,height,reflectionSize=ReflectionSize;
            public string intent,source,sourceSha256,authoringSourceSha256,visibleSha256,ambientPanoramaSha256,reflectionAsset,ambientAsset,colourSpace,recipe,discPolicy;
            public bool oldSunRemoved,streetlightsStartingOn=true;
            public float[] cityBounceLinear;
            public float[] sunDirectionLinear,sunColourLinear,zenithSrgb,lavenderSrgb,roseSrgb,peachSrgb,groundSrgb,fogColourSrgb;
            public float sunElevationDegrees,sunIrradiance,unitySunIntensity,environmentIntensity,skyRadianceScale,discRadiusDegrees,discEdgeDegrees,discPeakRadiance,sourceSkyMean,sourceSkyP50,sourceSkyP90,fogDensity=.0015f;
            public double discWeightSolidAngle;
            public float[] integratedDiscIrradiance;
            public NativeEnvironmentSun.SunReceipt originalSunExtraction;
            public CubemapCardinals.Sample[] reflectionCardinals;
        }
        [Serializable] sealed class AmbientSample {public float[] normal,rgb;public float whiteError,hemisphereError;}
        [Serializable] sealed class AmbientReceipt
        {
            public int version=1,samples=AmbientSamples;
            public bool whiteFurnacePass,hemispherePass;
            public string sourceSha256,orientedSha256,coefficientLayout,integration,nativeSunPolicy;
            public float environmentIntensity=EnvironmentIntensity,whiteNormalizer,maxWhiteFurnaceError,maxHemisphereError;
            public float[] coefficients,environmentCoefficients,hemisphereCoefficients,cityBounceLinear,cityBounceCoefficients;
            public float maxCityBounceError;
            public AmbientSample[] evaluations;
        }
        static string Hash(byte[] bytes){using(var sha=SHA256.Create())return BitConverter.ToString(sha.ComputeHash(bytes)).Replace("-","").ToLowerInvariant();}
        static float[] Rgb(Color c)=>new[]{c.r,c.g,c.b};
        static float[] Direction(Vector3 d)=>new[]{d.x,d.y,d.z};
        static float Luminance(Color c)=>.2126f*c.r+.7152f*c.g+.0722f*c.b;
        static bool Finite(float n)=>!float.IsNaN(n)&&!float.IsInfinity(n);
        static Vector3 PixelDirection(int x,int y,int width,int height){float longitude=(.5f-(x+.5f)/width)*2*Mathf.PI,latitude=((y+.5f)/height-.5f)*Mathf.PI,cl=Mathf.Cos(latitude);return new Vector3(cl*Mathf.Cos(longitude),Mathf.Sin(latitude),cl*Mathf.Sin(longitude));}
        static Vector3 SphereDirection(int i,int count){float y=1-2*(i+.5f)/count,r=Mathf.Sqrt(Mathf.Max(0,1-y*y)),a=i*2.399963229728653f;return new Vector3(Mathf.Cos(a)*r,y,Mathf.Sin(a)*r);}
        static float Smooth(float low,float high,float value){float t=Mathf.Clamp01((value-low)/(high-low));return t*t*(3-2*t);}
        static float[] Coefficients(SphericalHarmonicsL2 sh){var values=new float[27];for(int c=0;c<3;c++)for(int k=0;k<9;k++)values[c*9+k]=sh[c,k];return values;}
        static Texture2D Image(int width,int height,Color[] pixels){var image=new Texture2D(width,height,TextureFormat.RGBAFloat,false,true);image.wrapModeU=TextureWrapMode.Repeat;image.wrapModeV=TextureWrapMode.Clamp;image.SetPixels(pixels);image.Apply();return image;}
        static Cubemap ImportCube(string path,bool filtered){
            AssetDatabase.ImportAsset(path);var importer=(TextureImporter)AssetImporter.GetAtPath(path);importer.textureShape=TextureImporterShape.TextureCube;importer.generateCubemap=TextureImporterGenerateCubemap.Cylindrical;
            importer.maxTextureSize=ReflectionSize;importer.sRGBTexture=false;importer.isReadable=true;importer.mipmapEnabled=true;importer.filterMode=FilterMode.Trilinear;importer.textureCompression=TextureImporterCompression.Uncompressed;
            var settings=new TextureImporterSettings();importer.ReadTextureSettings(settings);settings.cubemapConvolution=filtered?TextureImporterCubemapConvolution.Specular:TextureImporterCubemapConvolution.None;importer.SetTextureSettings(settings);importer.SaveAndReimport();return AssetDatabase.LoadAssetAtPath<Cubemap>(path);
        }
        static Cubemap Reflection(Texture2D visible,Texture2D ambient){
            string rawPath=Scratch+"sunset-reflection-original.exr",roughPath=Scratch+"sunset-reflection-convolved.exr";var rawSource=CubemapCardinals.PrepareForCylindricalImport(visible);var roughSource=CubemapCardinals.PrepareForCylindricalImport(ambient);
            try{File.WriteAllBytes(rawPath,rawSource.EncodeToEXR(Texture2D.EXRFlags.CompressZIP));File.WriteAllBytes(roughPath,roughSource.EncodeToEXR(Texture2D.EXRFlags.CompressZIP));}finally{UnityEngine.Object.DestroyImmediate(rawSource);UnityEngine.Object.DestroyImmediate(roughSource);}
            var raw=ImportCube(rawPath,false);var rough=ImportCube(roughPath,true);if(!raw||!rough||raw.width!=rough.width||raw.mipmapCount!=rough.mipmapCount)throw new InvalidOperationException("Sunset reflection layout differs");
            var cube=new Cubemap(ReflectionSize,TextureFormat.RGBAHalf,true){name="Cinder authored evening reflection",filterMode=FilterMode.Trilinear,wrapMode=TextureWrapMode.Clamp};
            foreach(CubemapFace face in new[]{CubemapFace.PositiveX,CubemapFace.NegativeX,CubemapFace.PositiveY,CubemapFace.NegativeY,CubemapFace.PositiveZ,CubemapFace.NegativeZ})for(int mip=0;mip<raw.mipmapCount;mip++)cube.SetPixels((mip==0?raw:rough).GetPixels(face,mip),face,mip);
            cube.Apply(false,false);string path=Resource+"sunset-reflection.asset";var existing=AssetDatabase.LoadAssetAtPath<Cubemap>(path);if(existing){EditorUtility.CopySerialized(cube,existing);EditorUtility.SetDirty(existing);UnityEngine.Object.DestroyImmediate(cube);cube=existing;}else AssetDatabase.CreateAsset(cube,path);AssetDatabase.SaveAssets();return cube;
        }
        static AmbientReceipt Ambient(Texture2D clean,string sourceHash,string panoramaHash){
            var white=new SphericalHarmonicsL2();var sky=new SphericalHarmonicsL2();
            for(int i=0;i<AmbientSamples;i++){Vector3 d=SphereDirection(i,AmbientSamples);float u=Mathf.Repeat(.5f-Mathf.Atan2(d.z,d.x)/(2*Mathf.PI),1),v=1-Mathf.Acos(d.y)/Mathf.PI;Color radiance=clean.GetPixelBilinear(u,v);white.AddDirectionalLight(d,Color.white,1);sky.AddDirectionalLight(d,radiance,1);}
            var normals=new Vector3[70];normals[0]=Vector3.right;normals[1]=Vector3.left;normals[2]=Vector3.up;normals[3]=Vector3.down;normals[4]=Vector3.forward;normals[5]=Vector3.back;for(int i=0;i<64;i++)normals[6+i]=SphereDirection(i,64);
            var raw=new Color[70];white.Evaluate(normals,raw);float mean=0;for(int i=0;i<6;i++)mean+=(raw[i].r+raw[i].g+raw[i].b)/18;if(!Finite(mean)||mean<=0)throw new InvalidOperationException("Sunset ambient normalization invalid");float normalization=1/mean;white=white*normalization;sky=sky*(normalization*EnvironmentIntensity);
            // Preserve the calibrated native hemisphere component. The new sky,
            // supplies the evening colour. A bounded cool city-bounce component below
            // keeps shaded walls readable for the requested not-dark-yet mood.
            Color top=new Color(189/255f,212/255f,237/255f,1).linear*(.24f/Mathf.PI),bottom=new Color(106/255f,96/255f,78/255f,1).linear*(.24f/Mathf.PI);
            var constant=new SphericalHarmonicsL2();constant.AddAmbientLight(Color.white);var unit=new Color[1];constant.Evaluate(new[]{Vector3.up},unit);var up=new SphericalHarmonicsL2();up.AddDirectionalLight(Vector3.up,Color.white,1);var down=new SphericalHarmonicsL2();down.AddDirectionalLight(Vector3.down,Color.white,1);var yBasis=up+down*(-1);var axis=new Color[1];yBasis.Evaluate(new[]{Vector3.up},axis);var hemi=new SphericalHarmonicsL2();
            for(int c=0;c<3;c++)for(int k=0;k<9;k++)hemi[c,k]=constant[c,k]*(top[c]+bottom[c])*.5f/unit[0][c]+yBasis[c,k]*(top[c]-bottom[c])*.5f/axis[0][c];
            var whiteValues=new Color[70];var hemiValues=new Color[70];var combinedValues=new Color[70];white.Evaluate(normals,whiteValues);hemi.Evaluate(normals,hemiValues);var bounce=new SphericalHarmonicsL2();for(int c=0;c<3;c++)for(int k=0;k<9;k++)bounce[c,k]=constant[c,k]*CityBounceLinear[c]/unit[0][c];
            var bounceValues=new Color[70];bounce.Evaluate(normals,bounceValues);float bounceError=0;foreach(var value in bounceValues)for(int c=0;c<3;c++)bounceError=Mathf.Max(bounceError,Mathf.Abs(value[c]-CityBounceLinear[c]));if(bounceError>.00001f)throw new InvalidOperationException("Sunset city bounce calibration failed");
            var combined=sky+hemi+bounce;combined.Evaluate(normals,combinedValues);var rows=new AmbientSample[70];float whiteError=0,hemiError=0;
            for(int i=0;i<70;i++){Color expected=Color.LerpUnclamped(bottom,top,.5f*normals[i].y+.5f);float a=0,b=0;for(int c=0;c<3;c++){a=Mathf.Max(a,Mathf.Abs(whiteValues[i][c]-1));b=Mathf.Max(b,Mathf.Abs(hemiValues[i][c]-expected[c]));if(!Finite(combinedValues[i][c]))throw new InvalidOperationException("Sunset ambient SH nonfinite");}whiteError=Mathf.Max(whiteError,a);hemiError=Mathf.Max(hemiError,b);rows[i]=new AmbientSample{normal=Direction(normals[i]),rgb=Rgb(combinedValues[i]),whiteError=a,hemisphereError=b};}
            if(whiteError>.002f||hemiError>.0002f)throw new InvalidOperationException("Sunset ambient calibration failed");
            var coefficients=Coefficients(combined);foreach(float value in coefficients)if(!Finite(value))throw new InvalidOperationException("Sunset SH coefficient nonfinite");
            return new AmbientReceipt{sourceSha256=sourceHash,orientedSha256=panoramaHash,coefficientLayout="channel-major: channel*9+coefficient, Unity SphericalHarmonicsL2 order",integration="4096 uniform Fibonacci directions, Unity directional SH, white-furnace normalization, environment intensity0.65 plus unchanged native hemisphere linear hex colours*0.24/pi plus authored constant city bounce linear(0.075,0.11,0.16). L2 low-frequency approximation.",nativeSunPolicy="The old photographic sun is removed using native extraction. The authored evening disc is excluded by construction from SH/rough reflections, while visible sky/mirror mip0 retain it. One analytic directional light supplies the recorded irradiance.",whiteFurnacePass=true,hemispherePass=true,whiteNormalizer=normalization,maxWhiteFurnaceError=whiteError,maxHemisphereError=hemiError,coefficients=coefficients,environmentCoefficients=Coefficients(sky),hemisphereCoefficients=Coefficients(hemi),cityBounceLinear=Rgb(CityBounceLinear),cityBounceCoefficients=Coefficients(bounce),maxCityBounceError=bounceError,evaluations=rows};
        }
        public static void Run(){
            const string source=Resource+"sky.hdr";var importer=(TextureImporter)AssetImporter.GetAtPath(source);if(importer==null)throw new InvalidOperationException("Run the daylight bake before sunset");
            var original=AssetDatabase.LoadAssetAtPath<Texture2D>(source);if(!original||!original.isReadable)throw new InvalidOperationException("Daylight HDR must be readable from its existing bake");
            string root=Path.GetFullPath(Path.Combine(Application.dataPath,"../..")),sourceHash=Hash(File.ReadAllBytes(source));Color[] pixels=original.GetPixels();var rgba=new float[pixels.Length*4];for(int i=0;i<pixels.Length;i++){rgba[i*4]=pixels[i].r;rgba[i*4+1]=pixels[i].g;rgba[i*4+2]=pixels[i].b;rgba[i*4+3]=pixels[i].a;}
            var removed=NativeEnvironmentSun.Extract(original.width,original.height,rgba);removed.receipt.sourceSha256=sourceHash;removed.receipt.nativeSources=NativeEnvironmentSun.ValidateNativeSources(root);removed.receipt.nativeSourcesMatch=true;
            if(removed.clamped!=null)for(int i=0;i<pixels.Length;i++)pixels[i]=new Color(removed.clamped[i*4],removed.clamped[i*4+1],removed.clamped[i*4+2],removed.clamped[i*4+3]);
            Texture2D cleanSource=null,visible=null,ambient=null;
            try{
                cleanSource=Image(original.width,original.height,pixels);int width=original.width,height=original.height;var samples=new Color[pixels.Length];var luminances=new System.Collections.Generic.List<float>();double sum=0;const float rotation=3.4095478f/(2*Mathf.PI);
                for(int y=0;y<height;y++)for(int x=0;x<width;x++){int i=y*width+x;samples[i]=cleanSource.GetPixelBilinear(Mathf.Repeat(1-(x+.5f)/width+rotation,1),(y+.5f)/height);if(PixelDirection(x,y,width,height).y>.05f){float l=Luminance(samples[i]);luminances.Add(l);sum+=l;}}
                luminances.Sort();if(luminances.Count==0)throw new InvalidOperationException("Sunset sky source empty");float sourceMean=(float)(sum/luminances.Count),p50=luminances[luminances.Count/2],p90=luminances[(int)(luminances.Count*.9f)];
                var cleanPixels=new Color[pixels.Length];var discWeights=new float[pixels.Length];double weightOmega=0;Vector3 horizontalSun=new Vector3(SunDirectionLinear.x,0,SunDirectionLinear.z).normalized;
                for(int y=0;y<height;y++)for(int x=0;x<width;x++){
                    int i=y*width+x;Vector3 d=PixelDirection(x,y,width,height);float l=Luminance(samples[i]);float structure=Mathf.Clamp(Mathf.Pow(Mathf.Max(.001f,l/Mathf.Max(.001f,sourceMean)),.45f),.55f,1.4f),cloud=Smooth(p50,Mathf.Max(p50+.001f,p90),l);
                    Vector3 horizontal=new Vector3(d.x,0,d.z).normalized;float sunward=Mathf.Pow(Mathf.Clamp01(.5f+.5f*Vector3.Dot(horizontal,horizontalSun)),4),horizon=Mathf.Exp(-d.y*d.y/(.28f*.28f));
                    Color baseSky;
                    if(d.y>=0){baseSky=Color.Lerp(Lavender,Zenith,Smooth(.25f,.85f,d.y));baseSky=Color.Lerp(baseSky,Rose,horizon*.85f);float warm=Mathf.Exp(-(d.y-.12f)*(d.y-.12f)/(.24f*.24f))*sunward;baseSky=Color.Lerp(baseSky,Peach,warm*.95f);baseSky=baseSky*structure+Color.Lerp(Lavender,Peach,sunward)*cloud*.22f;}
                    else baseSky=Color.Lerp(Rose*.35f,Ground,Smooth(0,.65f,-d.y))*(.8f+.2f*structure);
                    float angle=Mathf.Acos(Mathf.Clamp(Vector3.Dot(d,SunDirectionLinear),-1,1))*Mathf.Rad2Deg;
                    float glow=Mathf.Exp(-angle*angle/(14f*14f))*.28f;baseSky=(baseSky+Peach*glow)*SkyRadianceScale;baseSky.a=1;cleanPixels[i]=baseSky;
                    float weight=1-Smooth(DiscRadiusDegrees-DiscEdgeDegrees,DiscRadiusDegrees+DiscEdgeDegrees,angle);discWeights[i]=weight;float solidAngle=Mathf.Cos(((y+.5f)/height-.5f)*Mathf.PI)*(2*Mathf.PI/width)*(Mathf.PI/height);weightOmega+=weight*solidAngle;
                }
                if(weightOmega<=0)throw new InvalidOperationException("Authored sunset disc has no source samples");float peak=(float)(SunIrradiance/weightOmega);var visiblePixels=(Color[])cleanPixels.Clone();double[] integrated=new double[3];
                for(int y=0;y<height;y++)for(int x=0;x<width;x++){int i=y*width+x;Color added=SunColourLinear*(peak*discWeights[i]);visiblePixels[i]+=added;visiblePixels[i].a=1;float omega=Mathf.Cos(((y+.5f)/height-.5f)*Mathf.PI)*(2*Mathf.PI/width)*(Mathf.PI/height);for(int c=0;c<3;c++)integrated[c]+=added[c]*omega;}
                visible=Image(width,height,visiblePixels);ambient=Image(width,height,cleanPixels);byte[] visibleBytes=visible.EncodeToEXR(Texture2D.EXRFlags.CompressZIP),ambientBytes=ambient.EncodeToEXR(Texture2D.EXRFlags.CompressZIP);Directory.CreateDirectory(Scratch);File.WriteAllBytes(Resource+"sunset-sky.exr",visibleBytes);File.WriteAllBytes(Scratch+"sunset-sky-ambient.exr",ambientBytes);
                AssetDatabase.ImportAsset(Resource+"sunset-sky.exr");var skyImporter=(TextureImporter)AssetImporter.GetAtPath(Resource+"sunset-sky.exr");skyImporter.sRGBTexture=false;skyImporter.maxTextureSize=1024;skyImporter.mipmapEnabled=false;skyImporter.filterMode=FilterMode.Bilinear;skyImporter.textureCompression=TextureImporterCompression.Uncompressed;skyImporter.SaveAndReimport();
                Cubemap reflection=Reflection(visible,ambient);var sh=Ambient(ambient,sourceHash,Hash(ambientBytes));File.WriteAllText(Resource+"sunset-ambient-sh.json",JsonUtility.ToJson(sh,true));
                var recipe=new Recipe{width=width,height=height,intent="Authored approximately 6pm golden hour: daylight-readable lowriders, blue/lavender zenith, rose/peach clouds and low warm sun; streetlights beginning to glow. Artistic scene profile, not an astronomical clock simulation.",source=source,sourceSha256=sourceHash,authoringSourceSha256=Hash(File.ReadAllBytes(Path.Combine(root,"Unity/Assets/Cinder/Scripts/Editor/CinderSunsetBake.cs"))),visibleSha256=Hash(visibleBytes),ambientPanoramaSha256=Hash(ambientBytes),reflectionAsset="Cinder/sunset-reflection",ambientAsset="Cinder/sunset-ambient-sh",colourSpace="Linear HDR source radiance. Palette constants are authored sRGB then .linear; light and environment intensity use existing calibrated API conventions.",recipe="Original native sun/halo extraction; orient native source; derive cloud structure pow(luminance/upper-sky mean,0.45), clamp0.55..1.4; cloudmask smoothstep(P50,P90); zenith smoothstep(altitude0.25..0.85); rose horizon exp(-y^2/0.28^2)*0.85; sunward pow((dot(horizontal,sun)+1)/2,4); peach band exp(-(y-0.12)^2/0.24^2)*sunward*0.95; cloud tint0.22; glow exp(-angleDegrees^2/14^2)*0.28; radianceScale1.8. Lower hemisphere blends rose*0.35 to muted ground over altitude0..-0.65.",discPolicy="Visible and mirror mip0 only; radius0.35degrees with0.20degree softedge, discrete solid-angle normalization to SunIrradiance. Rough mips1+ and diffuseSH share the identical authored disc-free sky. No second sun contribution.",oldSunRemoved=removed.receipt.found,cityBounceLinear=Rgb(CityBounceLinear),sunDirectionLinear=Direction(SunDirectionLinear),sunColourLinear=Rgb(SunColourLinear),zenithSrgb=new[]{.25f,.37f,.62f},lavenderSrgb=new[]{.42f,.46f,.72f},roseSrgb=new[]{.84f,.43f,.57f},peachSrgb=new[]{1f,.67f,.43f},groundSrgb=new[]{.25f,.22f,.24f},fogColourSrgb=new[]{.66f,.59f,.64f},sunElevationDegrees=Mathf.Asin(SunDirectionLinear.y)*Mathf.Rad2Deg,sunIrradiance=SunIrradiance,unitySunIntensity=UnitySunIntensity,environmentIntensity=EnvironmentIntensity,skyRadianceScale=SkyRadianceScale,discRadiusDegrees=DiscRadiusDegrees,discEdgeDegrees=DiscEdgeDegrees,discPeakRadiance=peak,discWeightSolidAngle=weightOmega,integratedDiscIrradiance=new[]{(float)integrated[0],(float)integrated[1],(float)integrated[2]},sourceSkyMean=sourceMean,sourceSkyP50=p50,sourceSkyP90=p90,originalSunExtraction=removed.receipt,reflectionCardinals=CubemapCardinals.Read(visible,reflection)};
                File.WriteAllText(Resource+"sunset-lighting.json",JsonUtility.ToJson(recipe,true));AssetDatabase.Refresh();AssetDatabase.SaveAssets();Debug.Log("SUNSET CPU BAKE oldSunRemoved="+recipe.oldSunRemoved+" elevation="+recipe.sunElevationDegrees+" whiteFurnace="+sh.maxWhiteFurnaceError+" hemi="+sh.maxHemisphereError);
            }finally{if(cleanSource)UnityEngine.Object.DestroyImmediate(cleanSource);if(visible)UnityEngine.Object.DestroyImmediate(visible);if(ambient)UnityEngine.Object.DestroyImmediate(ambient);}
        }
    }
}
