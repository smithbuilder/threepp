using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using UnityEditor;
using UnityEngine;

namespace Cinder.Editor
{
    // Diagnostic authoring only. Does not open shader/editor windows or change
    // shader source, materials, compiled variants, cameras or player settings.
    public static class SurfaceShaderDiagnostics
    {
        [Serializable] sealed class Report
        {
            public string unity,createdUtc,shader,sourcePath,sourceSha256,scope;
            public bool success;
            public int subshaders;
            public List<PassRow> passes=new List<PassRow>();
            public List<string> errors=new List<string>();
        }
        [Serializable] sealed class PassRow
        {
            public int subshader,pass,characters;
            public string name,file,sha256;
            public bool grabPass,containsWorldNormalVector,containsNormalMapKeyword;
        }
        static string Hash(byte[] bytes)
        {
            using(var hash=SHA256.Create())
                return BitConverter.ToString(hash.ComputeHash(bytes)).Replace("-","").ToLowerInvariant();
        }
        public static bool Write(string outputDirectory)
        {
            if(string.IsNullOrWhiteSpace(outputDirectory))throw new ArgumentException("Diagnostic output directory is required");
            string directory=Path.GetFullPath(outputDirectory);
            if(Directory.Exists(directory)&&Directory.GetFileSystemEntries(directory).Length!=0)
                throw new InvalidOperationException("Preserve existing shader diagnostics and use a fresh candidate directory: "+directory);
            Directory.CreateDirectory(directory);
            var report=new Report
            {
                unity=Application.unityVersion,createdUtc=DateTime.UtcNow.ToString("o"),shader="Cinder/Body",
                scope="Generated surface-shader pass source from the pinned Editor API. Source inspection only; not GPU output or a fidelity PASS."
            };
            try
            {
                Shader shader=Shader.Find(report.shader);
                if(!shader)throw new InvalidOperationException("Missing shader "+report.shader);
                report.sourcePath=AssetDatabase.GetAssetPath(shader);
                report.sourceSha256=Hash(File.ReadAllBytes(report.sourcePath));
                MethodInfo sourceMethod=typeof(ShaderUtil).GetMethod("GetShaderPassSourceCode",
                    BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic,null,
                    new[]{typeof(Shader),typeof(int),typeof(int)},null);
                if(sourceMethod==null||sourceMethod.ReturnType!=typeof(string))
                    throw new MissingMethodException("Pinned ShaderUtil.GetShaderPassSourceCode(Shader,int,int) is unavailable");
                var data=ShaderUtil.GetShaderData(shader);
                report.subshaders=data.SubshaderCount;
                for(int si=0;si<data.SubshaderCount;si++)
                {
                    var subshader=data.GetSubshader(si);
                    for(int pi=0;pi<subshader.PassCount;pi++)
                    {
                        var pass=subshader.GetPass(pi);
                        var row=new PassRow{subshader=si,pass=pi,name=pass.Name,grabPass=pass.IsGrabPass};
                        report.passes.Add(row);
                        if(row.grabPass)continue;
                        string source=(string)sourceMethod.Invoke(null,new object[]{shader,si,pi});
                        if(string.IsNullOrEmpty(source))
                        {
                            report.errors.Add("Empty generated source for subshader "+si+" pass "+pi);
                            continue;
                        }
                        byte[] bytes=new UTF8Encoding(false).GetBytes(source);
                        row.file="subshader-"+si+"-pass-"+pi+".hlsl";
                        row.characters=source.Length;row.sha256=Hash(bytes);
                        row.containsWorldNormalVector=source.Contains("WorldNormalVector");
                        row.containsNormalMapKeyword=source.Contains("_NORMALMAP");
                        File.WriteAllBytes(Path.Combine(directory,row.file),bytes);
                    }
                }
                report.success=report.errors.Count==0&&report.passes.Exists(row=>row.characters>0);
            }
            catch(Exception exception)
            {
                var failure=exception is TargetInvocationException&&exception.InnerException!=null?exception.InnerException:exception;
                report.errors.Add(failure.ToString());report.success=false;
            }
            File.WriteAllText(Path.Combine(directory,"manifest.json"),JsonUtility.ToJson(report,true),new UTF8Encoding(false));
            Debug.Log("SURFACE SHADER DIAGNOSTICS success="+report.success+" passes="+report.passes.Count+" output="+directory);
            return report.success;
        }
    }
}
