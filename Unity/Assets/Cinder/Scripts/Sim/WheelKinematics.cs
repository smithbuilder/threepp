using System;
using static Cinder.Sim.SimMath;

namespace Cinder.Sim {
    public struct WheelPose {public DVec3 Low,High,Center,Hub,Rack;public DQuat Rotation;}
    public struct AxlePose {public DVec3 Center;public DQuat Rotation,Tube;public double ClosureError;}
    public static class WheelKinematics {
        public static double Steering(VehicleTune t,int i,double central) {
            if(i>1||Math.Abs(central)<.0001)return 0;double radius=2*t.HalfWheelbase/Math.Tan(Math.Abs(central));bool inner=(central>0)==(i%2==1);return Math.Sign(central)*Math.Atan2(2*t.HalfWheelbase,radius+(inner?-t.HalfTrack:t.HalfTrack));
        }
        public static DVec3 Hub(VehicleTune t,int i,double[] travel,double steering) {return Pose(t,i,travel,steering).Hub;}
        public static WheelPose Pose(VehicleTune t,int i,double[] travel,double steering) {
            if(t.Id=="baja"){if(i<2)return BajaFront(i,travel[i],steering);AxlePose a=BajaRear(travel[2],travel[3]);return new WheelPose{Center=a.Center,Hub=a.Center+a.Rotation.Rotate(new DVec3(i==2?-1.025:1.025,0,0)),Rotation=a.Rotation};}
            if(t.Id=="switchback")return Switchback(i,travel[i],steering);
            if(t.Id=="catrina"){if(i<2)return CatrinaFront(i,travel[i],steering);AxlePose a=CatrinaRear(travel[2],travel[3]);return new WheelPose{Center=a.Center,Hub=a.Center+a.Rotation.Rotate(new DVec3(i==2?-.755:.755,0,0)),Rotation=a.Rotation};}
            if(t.Id=="media-luna"){if(i<2)return LunaFront(i,travel[i],steering);AxlePose a=LunaRear(travel[2],travel[3]);return new WheelPose{Center=a.Center,Hub=a.Center+a.Rotation.Rotate(new DVec3(i==2?-.74:.74,0,0)),Rotation=a.Rotation};}
            if(t.Id=="nocturne"){if(i<2)return NocturneFront(i,travel[i],steering);AxlePose a=NocturneRear(travel[2],travel[3]);return new WheelPose{Center=a.Center,Hub=a.Center+a.Rotation.Rotate(new DVec3(i==2?-.785:.785,0,0)),Rotation=a.Rotation};}
            double x=(i%2!=0?1:-1)*t.TrackAt(i),z=(i<2?1:-1)*t.HalfWheelbase,y=travel[i];
            if(!t.StraightWheelPath){double dy=Clamp(y,t.Droop,t.Bump)-.46;if(i>1)z=-t.HalfWheelbase+1.05-Math.Sqrt(Math.Max(0,1.05*1.05-dy*dy));else x=(i%2!=0?1:-1)*(t.ArmPivotX+Math.Sqrt(Math.Max(0,.50249378*.50249378-dy*dy))+.20);}
            DVec3 low=new DVec3(x-(i%2!=0?1:-1)*.20,y-.10,z);
            return new WheelPose {Hub=new DVec3(x,y,z),Low=low,High=low+new DVec3(0,.36,0),Center=low+new DVec3(0,.18,0),Rotation=DQuat.AxisAngle(DVec3.Up,Steering(t,i,steering))};
        }
        static WheelPose BajaEvaluate(double y) {
            double lowX=.68+Math.Sqrt(Math.Max(.00001,.29*.29+.04*.04-Sqr(y-.27)));DVec3 low=new DVec3(lowX,y,0),anchor=new DVec3(.70,.40,0),delta=low-anchor;double d=delta.Length;delta/=d;
            double a=(.27*.27+.06*.06-.15*.15+d*d)/(2*d),h=Math.Sqrt(Math.Max(0,.27*.27+.06*.06-a*a));DVec3 basis=anchor+delta*a,perp=new DVec3(-delta.Y,delta.X,0),p=basis+perp*h,q=basis-perp*h,upper=p.Y>=q.Y?p:q;
            double angle=-Math.Atan2(upper.X-low.X,upper.Y-low.Y);return new WheelPose{Low=low,High=upper,Hub=new DVec3(low.X+.055*Math.Cos(angle)-.09*Math.Sin(angle),low.Y+.055*Math.Sin(angle)+.09*Math.Cos(angle),0),Rotation=DQuat.AxisAngle(new DVec3(0,0,1),angle)};
        }
        public static WheelPose BajaFront(int i,double target,double steering) {
            double y=Clamp(target-.09,.12,.45);for(int n=0;n<6;n++){WheelPose p=BajaEvaluate(y);double derivative=(BajaEvaluate(y+.0001).Hub.Y-p.Hub.Y)/.0001;y=Clamp(y+(target-p.Hub.Y)/Math.Max(.2,derivative),.12,.45);}
            WheelPose pose=BajaEvaluate(y);double s=i%2!=0?1:-1;pose.Low=new DVec3(pose.Low.X*s,pose.Low.Y,1.59);pose.High=new DVec3(pose.High.X*s,pose.High.Y,1.59);
            double angle=-Math.Atan2(pose.High.X-pose.Low.X,pose.High.Y-pose.Low.Y);pose.Rotation=DQuat.AxisAngle(new DVec3(0,0,1),angle)*DQuat.AxisAngle(DVec3.Up,Steering(VehicleCatalog.Get(2),i,steering));pose.Hub=pose.Low+pose.Rotation.Rotate(new DVec3(s*.055,.09,0));return pose;
        }
        public static AxlePose BajaRear(double left,double right) {
            double roll=Math.Asin(Clamp((right-left)/2.05,-.25,.25)),c=Math.Cos(roll),s=Math.Sin(roll),y=(left+right)*.5;
            double panY=y+.76*s+.03*c,panOffset=.76*c-.03*s,x=-.72+Math.Sqrt(Math.Max(.1,1.48*1.48+.15*.15-Sqr(panY-.58)))-panOffset,z=0;
            foreach(int sign in new[]{-1,1})foreach(double yy in new[]{-.09,.09}){double dx=x+sign*.77*c-yy*s-sign*.64,dy=y+sign*.77*s+yy*c-(yy>0?.48:.30);z+=-.72-Math.Sqrt(Math.Max(.1,.13*.13+.01*.01+.87*.87-dx*dx-dy*dy));}
            return new AxlePose{Center=new DVec3(x,y,z*.25),Rotation=DQuat.AxisAngle(new DVec3(0,0,1),roll)};
        }
        public static WheelPose Switchback(int i,double height,double steering) {
            double s=i%2!=0?1:-1;
            if(i<2){double dy=Clamp(height-.31,-.05,.075);DVec3 ball=new DVec3(s*(.30+Math.Sqrt(.434*.434-dy*dy)),.255+dy,1.24),top=new DVec3(s*.54,.84,1.22),axis=(top-ball).Normalized;DQuat yaw=DQuat.AxisAngle(axis,Steering(VehicleCatalog.Get(3),i,steering));return new WheelPose{Low=ball,High=top,Center=ball,Hub=yaw.Rotate(new DVec3(s*.076,.055,0))+ball,Rotation=yaw};}
            double rearDy=Clamp(height-.31,-.056,.084),r=Hypot(.02,.58),angle=Math.Asin(Clamp((-.02+rearDy)/r,-1,1))-Math.Asin(-.02/r);DQuat q=DQuat.AxisAngle(new DVec3(1,0,0),angle);DVec3 pivot=new DVec3(s*.68,.33,-.66),hub=q.Rotate(new DVec3(s*.81,.31,-1.24)-pivot)+pivot;return new WheelPose{Low=pivot,High=hub,Hub=hub,Rotation=q,Center=pivot};
        }
        public static WheelPose CatrinaFront(int i,double height,double steering) {
            double s=i!=0?1:-1,target=Clamp(height,-.12,.42),dy=target-.2891,span=Math.Sqrt(Math.Max(.0001,.535*.535-dy*dy));DVec3 low=new DVec3(s*(.18+span),.25+dy,1.5113),high=new DVec3(low.X,.43+dy,low.Z);DQuat q=DQuat.AxisAngle(DVec3.Up,Steering(VehicleCatalog.Get(4),i,steering));return new WheelPose{Low=low,High=high,Hub=low+q.Rotate(new DVec3(s*.05,.0391,0)),Rotation=q,Center=(low+high)*.5};
        }
        public static DVec3 CatrinaRearBody(int j) {return j<2?new DVec3(j==0?-.56:.56,.33,-.45):j==2?new DVec3(0,.46,-.45):new DVec3(-.60,.62,-1.30);}
        public static DVec3 CatrinaRearEnd(int j) {return j<2?new DVec3(j==0?-.56:.56,.33,-1.5113):j==2?new DVec3(0,.42,-1.5113):new DVec3(.56,.35,-1.30);}
        static AxlePose CatrinaAxlePose(double[] x,double left,double right) {double roll=Math.Asin(Clamp((right-left)/1.51,-.99,.99));return new AxlePose{Center=new DVec3(x[0],(left+right)*.5,x[1]),Rotation=DQuat.AxisAngle(DVec3.Up,x[2])*DQuat.AxisAngle(new DVec3(0,0,1),roll)*DQuat.AxisAngle(new DVec3(1,0,0),x[3])};}
        static double[] CatrinaResidual(double[] x,double left,double right) {AxlePose a=CatrinaAxlePose(x,left,right);double[] f=new double[4];for(int j=0;j<4;j++){DVec3 b=CatrinaRearBody(j),end=CatrinaRearEnd(j);f[j]=(a.Rotation.Rotate(end-new DVec3(0,.2891,-1.5113))+a.Center-b).Length-(end-b).Length;}return f;}
        public static AxlePose CatrinaRear(double left,double right) {
            left=Clamp(left,-.28,.42);right=Clamp(right,-.28,.42);double[] x={0,-1.5113,0,0};
            for(int iter=0;iter<24;iter++){double[] f=CatrinaResidual(x,left,right);double error=0;foreach(double v in f)error=Math.Max(error,Math.Abs(v));if(error<.000002)break;double[,] matrix=new double[4,5];for(int row=0;row<4;row++)matrix[row,4]=-f[row];for(int col=0;col<4;col++){double[] v=(double[])x.Clone();v[col]+=.001;double[] ff=CatrinaResidual(v,left,right);for(int row=0;row<4;row++)matrix[row,col]=(ff[row]-f[row])/.001;}if(!Solve4(matrix,x,.15))break;}
            AxlePose p=CatrinaAxlePose(x,left,right);foreach(double v in CatrinaResidual(x,left,right))p.ClosureError=Math.Max(p.ClosureError,Math.Abs(v));return p;
        }
        static bool Solve4(double[,] a,double[] x,double limit) {for(int col=0;col<4;col++){int best=col;for(int row=col+1;row<4;row++)if(Math.Abs(a[row,col])>Math.Abs(a[best,col]))best=row;if(Math.Abs(a[best,col])<1e-7)return false;for(int k=col;k<5;k++){double swap=a[col,k];a[col,k]=a[best,k];a[best,k]=swap;}double d=a[col,col];for(int k=col;k<5;k++)a[col,k]/=d;for(int row=0;row<4;row++)if(row!=col){double m=a[row,col];for(int k=col;k<5;k++)a[row,k]-=m*a[col,k];}}for(int col=0;col<4;col++)x[col]+=Clamp(a[col,4],-limit,limit);return true;}
        public static WheelPose LunaFront(int i,double height,double steering) {
            double side=i!=0?1:-1;WheelPose p=new WheelPose();p.Rack=new DVec3(side*.10+.16*Math.Sin(steering),.25,1.4732+.16);double lo=-.18,hi=.47;
            for(int step=0;step<18;step++){
                double y=(lo+hi)*.5,x=.10+Math.Sqrt(Math.Max(0,.2501-Sqr(y-.25))),dx=x-.12,dy=y-.484,d=Hypot(dx,dy),radiusSq=.48*.48+.004*.004;
                double along=(radiusSq-.24*.24+d*d)/(2*d),across=Math.Sqrt(Math.Max(0,radiusSq-along*along));
                p.Low=new DVec3(side*x,y,1.4732);p.High=new DVec3(side*(.12+(along*dx-across*dy)/d),.484+(along*dy+across*dx)/d,1.4732);p.Center=(p.Low+p.High)*.5;
                p.Rotation=DQuat.FromTo(DVec3.Up,(p.High-p.Low).Normalized);DVec3 anchor=p.Rotation.Inverse.Rotate(p.Rack-p.Center);
                double c=(anchor.LengthSquared+.12*.12+.16*.16-.2501+2*.12*anchor.Y)/.32;
                double yaw=Math.Atan2(anchor.X,anchor.Z)+side*Math.Acos(Clamp(c/Math.Max(1e-12,Hypot(anchor.X,anchor.Z)),-1,1));
                p.Rotation=p.Rotation*DQuat.AxisAngle(DVec3.Up,yaw);p.Hub=p.Rotation.Rotate(new DVec3(side*.13,-.01575,0))+p.Center;
                if(p.Hub.Y<height)lo=y;else hi=y;
            }return p;
        }
        public static AxlePose LunaRear(double left,double right) {
            DVec3 ball=new DVec3(0,.40,.42),rest=new DVec3(0,.34425,-1.4732);double dy=(left+right)*.5-ball.Y;
            AxlePose p=new AxlePose();p.Center=new DVec3(0,ball.Y+dy,ball.Z-Math.Sqrt(Math.Max(0,(rest-ball).LengthSquared-dy*dy)));p.Tube=DQuat.FromTo((rest-ball).Normalized,(p.Center-ball).Normalized);
            p.Rotation=DQuat.AxisAngle(new DVec3(0,0,1),Math.Asin(Clamp((right-left)/(2*.74),-1,1)))*p.Tube;return p;
        }
        public static WheelPose NocturneFront(int i,double height,double steering) {
            double s=i!=0?1:-1;DVec3 restAxis=new DVec3(-s*.02,.24,0),lever=new DVec3(0,-.09,.16),kingpin=restAxis.Normalized;
            double upright=restAxis.Length,lowerRadius=Hypot(.34,.02),upperRadius=Hypot(.28,.05);WheelPose p=new WheelPose();p.Rack=new DVec3(s*.28+.12*Math.Sin(steering),.32,1.8002);double lo=.10,hi=.47;
            for(int step=0;step<22;step++) {
                double y=(lo+hi)*.5,x=.34+Math.Sqrt(Math.Max(0,lowerRadius*lowerRadius-Sqr(y-.29))),dx=x-.38,dy=y-.56,d=Hypot(dx,dy);
                double along=(upperRadius*upperRadius-upright*upright+d*d)/(2*d),across=Math.Sqrt(Math.Max(0,upperRadius*upperRadius-along*along));
                p.Low=new DVec3(s*x,y,1.6002);p.High=new DVec3(s*(.38+(along*dx-across*dy)/d),.56+(along*dy+across*dx)/d,1.6002);p.Center=(p.Low+p.High)*.5;
                DQuat tilt=DQuat.FromTo(kingpin,(p.High-p.Low).Normalized);DVec3 anchor=tilt.Inverse.Rotate(p.Rack-p.Center);double axial=DVec3.Dot(lever,kingpin),tieLengthSq=.39*.39+.02*.02+.04*.04;
                DVec3 planar=lever-kingpin*axial,crossed=DVec3.Cross(kingpin,lever);double a=DVec3.Dot(anchor,planar),b=DVec3.Dot(anchor,crossed),c=(anchor.LengthSquared+lever.LengthSquared-tieLengthSq)*.5-DVec3.Dot(anchor,kingpin)*axial;
                double phase=Math.Atan2(b,a),sweep=Math.Acos(Clamp(c/Math.Max(1e-12,Hypot(a,b)),-1,1)),yaw1=Math.IEEERemainder(phase+sweep,2*Math.PI),yaw2=Math.IEEERemainder(phase-sweep,2*Math.PI),desired=Steering(VehicleCatalog.Get(6),i,steering);
                double yaw=Math.Abs(yaw1-desired)<Math.Abs(yaw2-desired)?yaw1:yaw2;p.Rotation=tilt*DQuat.AxisAngle(kingpin,yaw);p.Hub=p.Rotation.Rotate(new DVec3(s*.12,-.042,0))+p.Center;if(p.Hub.Y<height)lo=y;else hi=y;
            }return p;
        }
        public static DVec3 NocturneRearBody(int j) {double s=j%2!=0?1:-1;return j<2?new DVec3(s*.58,.24,-.64):new DVec3(s*.48,.40,-.80);}
        public static DVec3 NocturneRearEnd(int j) {double s=j%2!=0?1:-1;return j<2?new DVec3(s*.58,.26,-1.6002):new DVec3(s*.22,.53,-1.6002);}
        static AxlePose NocturneAxlePose(double[] v,double left,double right) {double usable=2*.785*Math.Cos(v[3]);DQuat roll=DQuat.AxisAngle(new DVec3(0,0,1),Math.Asin(Clamp((right-left)/usable,-.85,.85)));return new AxlePose{Center=new DVec3(v[0],(left+right)*.5,v[1]),Rotation=roll*DQuat.AxisAngle(DVec3.Up,v[3])*DQuat.AxisAngle(new DVec3(1,0,0),v[2])};}
        static double[] NocturneResidual(double[] v,double left,double right) {AxlePose a=NocturneAxlePose(v,left,right);DVec3 rest=new DVec3(0,.348,-1.6002);double[] f=new double[4];for(int j=0;j<4;j++){DVec3 body=NocturneRearBody(j),end=NocturneRearEnd(j);f[j]=(a.Rotation.Rotate(end-rest)+a.Center-body).Length-(end-body).Length;}return f;}
        public static AxlePose NocturneRear(double left,double right) {
            double[] x={0,-1.6002,0,0};
            for(int iter=0;iter<12;iter++) {
                double[] f=NocturneResidual(x,left,right);double error=0;foreach(double v in f)error=Math.Max(error,Math.Abs(v));if(error<.0000003)break;
                double[,] a=new double[4,5];for(int row=0;row<4;row++)a[row,4]=-f[row];
                for(int col=0;col<4;col++){double[] v=(double[])x.Clone();v[col]+=.0001;double[] ff=NocturneResidual(v,left,right);for(int row=0;row<4;row++)a[row,col]=(ff[row]-f[row])/.0001;}
                bool singular=false;
                for(int col=0;col<4;col++) {
                    int best=col;for(int row=col+1;row<4;row++)if(Math.Abs(a[row,col])>Math.Abs(a[best,col]))best=row;if(Math.Abs(a[best,col])<1e-7){singular=true;break;}
                    for(int k=col;k<5;k++){double swap=a[col,k];a[col,k]=a[best,k];a[best,k]=swap;}double divisor=a[col,col];for(int k=col;k<5;k++)a[col,k]/=divisor;
                    for(int row=0;row<4;row++)if(row!=col){double m=a[row,col];for(int k=col;k<5;k++)a[row,k]-=m*a[col,k];}
                }
                if(singular)break;for(int col=0;col<4;col++)x[col]+=Clamp(a[col,4],-.08,.08);
            }
            AxlePose p=NocturneAxlePose(x,left,right);double[] final=NocturneResidual(x,left,right);foreach(double v in final)p.ClosureError=Math.Max(p.ClosureError,Math.Abs(v));return p;
        }
    }
}
