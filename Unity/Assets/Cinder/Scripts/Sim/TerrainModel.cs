using System;
using static Cinder.Sim.SimMath;

namespace Cinder.Sim {
    [Serializable] public sealed class Station {
        public string Name {get; private set;} public double X {get; private set;} public double Z {get; private set;} public double Yaw {get; private set;} public double DefaultSpeed {get; private set;} public double EndZ {get; private set;}
        public Station(string name,double x,double z,double speed=2.2,double end=102) {Name=name;X=x;Z=z;DefaultSpeed=speed;EndZ=end;}
    }
    [Serializable] public struct WorldSolid {
        public DVec3 Center,HalfSize;public string Name;
        public WorldSolid(double x,double y,double z,double hx,double hy,double hz,string name="") {Center=new DVec3(x,y,z);HalfSize=new DVec3(hx,hy,hz);Name=name;}
    }
    public sealed class TerrainModel {
        public const int Nx=264,Nz=440;public const double Step=.5,MinX=-66,MinZ=-24;
        public readonly bool City;
        readonly double[] heights;
        static double[] playgroundCache,cityCache;
        static readonly Station[] stations={new Station("Level pad",-50,-10),new Station("Cross-axle ruts",-50,18),new Station("Bumps and whoops",-25,14),new Station("Steep climb / descent",0,9),new Station("Narrow ridge",25,10),new Station("Side slope",50,18),new Station("Jump line",-50,94,10,183),new Station("Wind tunnel",25,137,0,160)};
        static readonly WorldSolid[] buildings={
            new WorldSolid(-13,7.36,49,9,7.2,9,"CORNER / COFFEE"),new WorldSolid(-13,10.56,71,9,10.4,11,"MERCER / LOFTS"),new WorldSolid(-13,5.76,94,9,5.6,8,"NORTH / SUPPLY"),new WorldSolid(14,5.56,52,8,5.4,12,"CINDER / MOTOR WORKS"),new WorldSolid(14,8.96,84,8,8.8,18,"BAY / WAREHOUSE"),new WorldSolid(-55,9.16,49,8.5,9,12,"WEST / STUDIOS"),new WorldSolid(-55,12.66,85,8.5,12.5,19,"MERCER / HOUSE"),new WorldSolid(55,10.66,52,8.5,10.5,15,"EAST / HOUSE"),new WorldSolid(55,7.16,93,8.5,7,14,"DOCK / STORAGE"),new WorldSolid(-16,11.66,142,19,11.5,12,"NORTH / MILL"),new WorldSolid(32,15.66,145,14,15.5,15,"THE / EXCHANGE")};
        static readonly WorldSolid[] windFrame={new WorldSolid(17,1.9,131,.1,1.9,.1),new WorldSolid(33,1.9,131,.1,1.9,.1),new WorldSolid(17,1.9,143,.1,1.9,.1),new WorldSolid(33,1.9,143,.1,1.9,.1),new WorldSolid(25,3.8,131,8,.1,.1),new WorldSolid(25,3.8,143,8,.1,.1),new WorldSolid(17,3.8,137,.1,.1,6),new WorldSolid(33,3.8,137,.1,.1,6)};
        readonly WorldSolid[] solids;
        public WorldSolid[] Solids {get {return (WorldSolid[])solids.Clone();}}
        internal WorldSolid[] CollisionSolids {get {return solids;}}
        public static Station[] Stations {get {return (Station[])stations.Clone();}}
        public static WorldSolid[] Buildings {get {return (WorldSolid[])buildings.Clone();}}
        public static WorldSolid[] WindFrame {get {return (WorldSolid[])windFrame.Clone();}}
        internal static Station StationAt(int i) {return stations[i];}
        public TerrainModel(bool city=false) {
            City=city;heights=city?cityCache:playgroundCache;
            if(heights==null){heights=new double[(Nx+1)*(Nz+1)];for(int z=0;z<=Nz;z++)for(int x=0;x<=Nx;x++)heights[z*(Nx+1)+x]=city?CitySurface(MinX+x*Step,MinZ+z*Step):Design(MinX+x*Step,MinZ+z*Step);if(city)cityCache=heights;else playgroundCache=heights;}
            if(city){solids=new WorldSolid[buildings.Length+4];Array.Copy(buildings,solids,buildings.Length);solids[11]=new WorldSolid(-65,1,85,.5,1,109);solids[12]=new WorldSolid(65,1,85,.5,1,109);solids[13]=new WorldSolid(0,1,-23,65,1,.5);solids[14]=new WorldSolid(0,1,195,65,1,.5);}else solids=windFrame;
        }
        public double VertexHeight(int x,int z) {return heights[z*(Nx+1)+x];}
        public double Height(double x,double z) {
            double gx=Clamp((x-MinX)/Step,0,Nx-.0001),gz=Clamp((z-MinZ)/Step,0,Nz-.0001);int ix=(int)gx,iz=(int)gz;double u=gx-ix,v=gz-iz;int a=iz*(Nx+1)+ix;
            double h00=heights[a],h10=heights[a+1],h01=heights[a+Nx+1],h11=heights[a+Nx+2];return u+v<=1?h00+(h10-h00)*u+(h01-h00)*v:h11+(h01-h11)*(1-u)+(h10-h11)*(1-v);
        }
        public DVec3 Normal(double x,double z) {
            double gx=Clamp((x-MinX)/Step,0,Nx-.0001),gz=Clamp((z-MinZ)/Step,0,Nz-.0001);int ix=(int)gx,iz=(int)gz,a=iz*(Nx+1)+ix;double u=gx-ix,v=gz-iz;
            return (u+v<=1?new DVec3(-(heights[a+1]-heights[a])/Step,1,-(heights[a+Nx+1]-heights[a])/Step):new DVec3(-(heights[a+Nx+2]-heights[a+Nx+1])/Step,1,-(heights[a+Nx+2]-heights[a+1])/Step)).Normalized;
        }
        public static double TrailCenter(int station,double z) {return station==4?25+1.4*Math.Sin((z-12)*.055)*Window(12,25,85,105,z):stations[station].X;}
        static double RoundedRamp(double x) {return x<=0?0:x<.7?x*x/1.4:x-.35;}
        static double Kicker(double z,double start,double lip,double h) {return h*(RoundedRamp(z-start)-RoundedRamp(z-lip))/(lip-start)*(1-Smooth(lip+.7,lip+1.8,z));}
        public static double Design(double x,double z) {
            double y=.018*Math.Sin(x*.37)*Math.Sin(z*.41)*Window(5,12,100,114,z),track=Window(17,21,82,90,z);
            for(int n=0;n<9;n++){double side=n%2!=0?1:-1,zz=28+n*5;y+=.22*Math.Exp(-Sqr((x+50-side*1.05)/.75)-Sqr((z-zz)/1.25));}
            y-=.08*track*Math.Exp(-Sqr((Math.Abs(x+50)-1.05)/.36));double lane=Math.Exp(-Math.Pow((x+25)/3.8,8));
            y+=lane*(.055*Math.Sin((z-20)*5.23599)*Window(16,20,36,40,z)+.24*Math.Sin((z-44)*.785398)*Window(40,45,82,90,z));
            y+=13*Smooth(12,43,z)*(1-Smooth(49,83,z))*Math.Exp(-Math.Pow(x/7,6));
            y+=10*Smooth(12,43,z)*(1-Smooth(70,102,z))*(1-Smooth(1.8,8,Math.Abs(x-TrailCenter(4,z))));
            y+=(x-50)*.404*Math.Exp(-Math.Pow((x-50)/6.5,8))*Window(20,34,78,93,z);
            y+=Math.Exp(-Math.Pow((x+50)/4.7,8))*(Kicker(z,110,114,1.3)+.40*Smooth(120,123,z)*(1-Smooth(123,134,z))+Kicker(z,150,156,2.5)+.75*Smooth(163,167,z)*(1-Smooth(167,181,z)));return y;
        }
        static double Edge(double v,double lo,double hi) {return Clamp(Math.Min(v-lo,hi-v)*2,0,1);}
        public static double CitySurface(double x,double z) {return .16*Math.Max(Math.Max(Edge(x,-25,25)*Edge(z,35,105),Edge(x,-66,-43)*Edge(z,35,105)),Math.Max(Edge(x,43,66)*Edge(z,35,105),Math.Max(Edge(x,-66,66)*Edge(z,123,196),Edge(x,-66,66)*Edge(z,-24,17))));}
    }
}
