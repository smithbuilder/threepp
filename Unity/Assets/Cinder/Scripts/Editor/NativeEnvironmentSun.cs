using System;
using System.IO;
using System.Text;
using System.Security.Cryptography;
using System.Collections.Generic;

namespace Cinder.Editor
{
    // Managed transcription of the frozen native extractor. RGB arithmetic,
    // thresholds, unweighted fill mean and solid-angle energy accounting follow
    // EnvSunExtract.cpp; this class contains no Unity or graphics dependency.
    public static class NativeEnvironmentSun
    {
        const float Pi=3.14159265358979323846f,TwoPi=6.28318530717958647692f,Deg2Rad=Pi/180f;
        [Serializable] public sealed class SourceHash {public string path,sha256,normalizedSha256;}
        [Serializable] public sealed class SunReceipt
        {
            public bool found,nativeSourcesMatch;
            public int width,height,discTexels,fillTexels,cappedTexels;
            public float peakLuminance,meanLuminance,detectionThreshold,discThreshold,haloCapLuminance,angularRadiusDeg;
            public double discSolidAngle;
            public float[] fillRgb,directionNative,removedIrradianceRgb,directionWorld;
            public string sourceSha256,clampedSourceSha256,algorithm,policy;
            public SourceHash[] nativeSources;
        }
        public sealed class Result {public float[] clamped;public SunReceipt receipt;}
        static string Hash(byte[] bytes){using(var hash=SHA256.Create())return BitConverter.ToString(hash.ComputeHash(bytes)).Replace("-","").ToLowerInvariant();}
        public static SourceHash[] ValidateNativeSources(string root)
        {
            string[] paths={"src/threepp/renderers/common/EnvSunExtract.cpp","src/threepp/renderers/common/EnvSunExtract.hpp","src/threepp/renderers/gl/GLCubeMaps.cpp","src/threepp/renderers/GLRenderer.cpp"};
            string[] expected={"bd8c79c087ea721ff9f02d79cb5bb3c42be7d8c8eb1b06e583b5c8021593add3","e264fd58845624610dfaf91047b32819bdf6cec65deabffae5a7f214a4811d0b","07bdec8a6c79daa484ad8e469737acd7318a9c5aa2c882d1b893b6b04b246aef","98ac968b6cde554d8f69e6c72c65a89855d4a6ab87efa6c4b18d56cab990bbe6"};
            var rows=new SourceHash[paths.Length];
            for(int i=0;i<paths.Length;i++)
            {
                string path=Path.Combine(root,paths[i]);byte[] raw=File.ReadAllBytes(path);
                string normalized=Hash(Encoding.UTF8.GetBytes(File.ReadAllText(path).Replace("\r\n","\n")));
                if(normalized!=expected[i])throw new InvalidOperationException("Native environment source changed; re-audit managed port: "+paths[i]+" / "+normalized);
                rows[i]=new SourceHash{path=paths[i],sha256=Hash(raw),normalizedSha256=normalized};
            }
            return rows;
        }
        static float Luminance(float r,float g,float b)=>.2126f*r+.7152f*g+.0722f*b;
        static float Luminance(float[] pixels,int pixel)=>Luminance(pixels[pixel*4],pixels[pixel*4+1],pixels[pixel*4+2]);
        static void TexelDirection(int x,int y,int width,int height,out float dx,out float dy,out float dz,out float solidAngle)
        {
            float u=(x+.5f)/width,v=(y+.5f)/height,phi=(u-.5f)*TwoPi,latitude=(v-.5f)*Pi;
            float cl=(float)Math.Cos(latitude);dx=cl*(float)Math.Cos(phi);dy=(float)Math.Sin(latitude);dz=cl*(float)Math.Sin(phi);
            solidAngle=cl*(TwoPi/width)*(Pi/height);
        }
        public static Result Extract(int width,int height,float[] pixels)
        {
            var receipt=new SunReceipt{width=width,height=height,directionNative=new[]{0f,1f,0f},removedIrradianceRgb=new float[3],algorithm="Native EnvSunExtract.cpp: peak>max(200*mean,32); 8-degree disc above 5% peak; non-disc fill inside 16 degrees; halo cap64*mean; excess RGB solid-angle energy and weighted direction.",policy="GLCubeMaps rough levels use clamped source; mip0/background keep original. GLRenderer EnvSunPolicy.Auto suppresses analytic reinjection when a scene DirectionalLight already exists; the Unity afternoon sun remains the sole analytic sun."};
            var result=new Result{receipt=receipt};
            if(pixels==null||width<=1||height<=1)return result;
            int count=checked(width*height);if(pixels.Length<count*4)throw new ArgumentException("Native sun extractor requires float RGBA pixels");
            float maximum=0;int maximumIndex=0;double sum=0;
            for(int i=0;i<count;i++){float lum=Luminance(pixels,i);sum+=lum;if(lum>maximum){maximum=lum;maximumIndex=i;}}
            float mean=(float)(sum/count);receipt.peakLuminance=maximum;receipt.meanLuminance=mean;receipt.detectionThreshold=Math.Max(200f*mean,32f);receipt.discThreshold=.05f*maximum;receipt.haloCapLuminance=64f*mean;
            if(maximum<=receipt.detectionThreshold)return result;
            TexelDirection(maximumIndex%width,maximumIndex/width,width,height,out float peakX,out float peakY,out float peakZ,out _);
            float cosRegion=(float)Math.Cos(8f*Deg2Rad),cosFill=(float)Math.Cos(16f*Deg2Rad),threshold=.05f*maximum;
            var fill=new double[3];int fillCount=0;var disc=new List<int>();
            for(int y=0;y<height;y++)for(int x=0;x<width;x++)
            {
                TexelDirection(x,y,width,height,out float dx,out float dy,out float dz,out _);
                float cosine=dx*peakX+dy*peakY+dz*peakZ;if(cosine<=cosFill)continue;
                int index=y*width+x;
                if(cosine>cosRegion&&Luminance(pixels,index)>threshold)disc.Add(index);
                else{for(int k=0;k<3;k++)fill[k]+=pixels[index*4+k];fillCount++;}
            }
            var replacement=new float[3];for(int k=0;k<3;k++)replacement[k]=fillCount>0?(float)(fill[k]/fillCount):0;
            receipt.fillRgb=replacement;receipt.fillTexels=fillCount;receipt.discTexels=disc.Count;
            var energy=new double[3];var direction=new double[3];double omega=0;
            foreach(int index in disc)
            {
                TexelDirection(index%width,index/width,width,height,out float dx,out float dy,out float dz,out float solidAngle);
                float exR=Math.Max(pixels[index*4]-replacement[0],0),exG=Math.Max(pixels[index*4+1]-replacement[1],0),exB=Math.Max(pixels[index*4+2]-replacement[2],0);
                float lum=Luminance(exR,exG,exB);
                energy[0]+=(double)exR*solidAngle;energy[1]+=(double)exG*solidAngle;energy[2]+=(double)exB*solidAngle;
                direction[0]+=(double)dx*lum*solidAngle;direction[1]+=(double)dy*lum*solidAngle;direction[2]+=(double)dz*lum*solidAngle;omega+=solidAngle;
            }
            double length=Math.Sqrt(direction[0]*direction[0]+direction[1]*direction[1]+direction[2]*direction[2]);
            receipt.discSolidAngle=omega;
            if(omega<=0||disc.Count==0||length<=1e-12||energy[0]+energy[1]+energy[2]<=1e-4)return result;
            var clamped=(float[])pixels.Clone();
            foreach(int index in disc)for(int k=0;k<3;k++)clamped[index*4+k]=replacement[k];
            float cap=64f*mean;int capped=0;
            for(int i=0;i<count;i++)
            {
                float lum=Luminance(clamped,i);if(lum<=cap)continue;
                TexelDirection(i%width,i/width,width,height,out float dx,out float dy,out float dz,out float solidAngle);
                float scale=cap/lum,exR=clamped[i*4]*(1-scale),exG=clamped[i*4+1]*(1-scale),exB=clamped[i*4+2]*(1-scale),exLum=Luminance(exR,exG,exB);
                energy[0]+=(double)exR*solidAngle;energy[1]+=(double)exG*solidAngle;energy[2]+=(double)exB*solidAngle;
                direction[0]+=(double)dx*exLum*solidAngle;direction[1]+=(double)dy*exLum*solidAngle;direction[2]+=(double)dz*exLum*solidAngle;
                for(int k=0;k<3;k++)clamped[i*4+k]*=scale;capped++;
            }
            length=Math.Sqrt(direction[0]*direction[0]+direction[1]*direction[1]+direction[2]*direction[2]);
            for(int k=0;k<3;k++){receipt.directionNative[k]=(float)(direction[k]/(length>1e-12?length:1));receipt.removedIrradianceRgb[k]=(float)energy[k];}
            receipt.angularRadiusDeg=Math.Min(10f,Math.Max(.05f,(float)Math.Sqrt((float)omega/Pi)/Deg2Rad));
            receipt.cappedTexels=capped;receipt.found=true;result.clamped=clamped;return result;
        }
    }
}
