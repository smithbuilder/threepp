using System;

namespace Cinder.Sim {
    // SI units. These value types deliberately have no engine dependency.
    [Serializable] public struct DVec3 {
        public double X,Y,Z;
        public DVec3(double x,double y,double z) { X=x;Y=y;Z=z; }
        public double LengthSquared { get { return X*X+Y*Y+Z*Z; } }
        public double Length { get { return Math.Sqrt(LengthSquared); } }
        public DVec3 Normalized { get { return this/Math.Max(1e-15,Length); } }
        public static DVec3 Zero { get { return new DVec3(); } }
        public static DVec3 Up { get { return new DVec3(0,1,0); } }
        public static DVec3 operator +(DVec3 a,DVec3 b) { return new DVec3(a.X+b.X,a.Y+b.Y,a.Z+b.Z); }
        public static DVec3 operator -(DVec3 a,DVec3 b) { return new DVec3(a.X-b.X,a.Y-b.Y,a.Z-b.Z); }
        public static DVec3 operator -(DVec3 a) { return a*-1; }
        public static DVec3 operator *(DVec3 a,double b) { return new DVec3(a.X*b,a.Y*b,a.Z*b); }
        public static DVec3 operator *(double b,DVec3 a) { return a*b; }
        public static DVec3 operator /(DVec3 a,double b) { return a*(1/b); }
        public static double Dot(DVec3 a,DVec3 b) { return a.X*b.X+a.Y*b.Y+a.Z*b.Z; }
        public static DVec3 Cross(DVec3 a,DVec3 b) { return new DVec3(a.Y*b.Z-a.Z*b.Y,a.Z*b.X-a.X*b.Z,a.X*b.Y-a.Y*b.X); }
    }
    [Serializable] public struct DQuat {
        public double X,Y,Z,W;
        public DQuat(double x,double y,double z,double w) { X=x;Y=y;Z=z;W=w; }
        public static DQuat Identity { get { return new DQuat(0,0,0,1); } }
        public DQuat Normalized { get { double n=Math.Sqrt(X*X+Y*Y+Z*Z+W*W);return n<1e-15?Identity:new DQuat(X/n,Y/n,Z/n,W/n); } }
        public DQuat Inverse { get { return new DQuat(-X,-Y,-Z,W); } }
        public DVec3 Rotate(DVec3 p) { DVec3 v=new DVec3(X,Y,Z),t=DVec3.Cross(v,p)*2;return p+t*W+DVec3.Cross(v,t); }
        public static DQuat operator *(DQuat a,DQuat b) { return new DQuat(a.W*b.X+a.X*b.W+a.Y*b.Z-a.Z*b.Y,a.W*b.Y-a.X*b.Z+a.Y*b.W+a.Z*b.X,a.W*b.Z+a.X*b.Y-a.Y*b.X+a.Z*b.W,a.W*b.W-a.X*b.X-a.Y*b.Y-a.Z*b.Z); }
        public static DQuat AxisAngle(DVec3 axis,double angle) { double s=Math.Sin(angle*.5);axis=axis.Normalized;return new DQuat(axis.X*s,axis.Y*s,axis.Z*s,Math.Cos(angle*.5)); }
        public static DQuat FromTo(DVec3 a,DVec3 b) { a=a.Normalized;b=b.Normalized;double d=DVec3.Dot(a,b);if(d<-.999999)return AxisAngle(Math.Abs(a.X)<.8?DVec3.Cross(a,new DVec3(1,0,0)):DVec3.Cross(a,DVec3.Up),Math.PI);DVec3 c=DVec3.Cross(a,b);return new DQuat(c.X,c.Y,c.Z,1+d).Normalized; }
    }
    public static class SimMath {
        public static double Clamp(double x,double a,double b) { return Math.Max(a,Math.Min(b,x)); }
        public static double Smooth(double a,double b,double x) { double t=Clamp((x-a)/(b-a),0,1);return t*t*(3-2*t); }
        public static double Window(double a,double b,double c,double d,double x) { return Smooth(a,b,x)*(1-Smooth(c,d,x)); }
        public static double Approach(double a,double b,double down,double up) { return a+Clamp(b-a,-down,up); }
        public static double Sqr(double a) { return a*a; }
        public static double Hypot(double a,double b) { return Math.Sqrt(a*a+b*b); }
    }
}
