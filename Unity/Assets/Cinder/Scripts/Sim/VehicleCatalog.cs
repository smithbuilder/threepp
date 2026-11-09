using System;

namespace Cinder.Sim {
    [Serializable] public sealed class VehicleTune {
        public string Id {get; private set;} public string Name {get; private set;}
        public double TyreRadius {get; private set;} public double TyreHalfWidth {get; private set;} public double HalfTrack {get; private set;} public double HalfWheelbase {get; private set;} public double Droop {get; private set;} public double Bump {get; private set;} public double ArmPivotX {get; private set;} public double StaticTravel {get; private set;}
        public double Mass {get; private set;} public double CgY {get; private set;} public double CgZ {get; private set;} public double Width {get; private set;} public double Height {get; private set;} public double Length {get; private set;} public double FrontRate {get; private set;} public double RearRate {get; private set;} public double Compression {get; private set;} public double Rebound {get; private set;} public double Grip {get; private set;} public double DriveForce {get; private set;}
        public double PitchInertia {get; private set;} public double YawInertia {get; private set;} public double RollInertia {get; private set;} public double HullBottom {get; private set;} public double NoseRise {get; private set;} public double TailRise {get; private set;}
        public bool StraightWheelPath {get; private set;} public bool RearWheelDrive {get; private set;}
        public double FrontalCdA {get; private set;} public double LateralCdA {get; private set;} public double VerticalCdA {get; private set;} public double PressureY {get; private set;} public double PressureZ {get; private set;}
        public double RearCompression {get; private set;} public double RearRebound {get; private set;} public double RearDroop {get; private set;} public double RearBump {get; private set;} public double RearHalfTrack {get; private set;} public double HullOffsetZ {get; private set;} public double HullFriction {get; private set;}
        internal VehicleTune(string id,string name,double[] d,double[] t,bool straight=false,double[] aero=null,double[] rear=null,bool rwd=false,double hullOffset=0,double hullFriction=.65) {
            Id=id;Name=name;TyreRadius=d[0];TyreHalfWidth=d[1];HalfTrack=d[2];HalfWheelbase=d[3];Droop=d[4];Bump=d[5];ArmPivotX=d[6];StaticTravel=d[7];
            Mass=t[0];CgY=t[1];CgZ=t[2];Width=t[3];Height=t[4];Length=t[5];FrontRate=t[6];RearRate=t[7];Compression=t[8];Rebound=t[9];Grip=t[10];DriveForce=t[11];PitchInertia=t[12];YawInertia=t[13];RollInertia=t[14];HullBottom=t[15];NoseRise=t[16];TailRise=t[17];StraightWheelPath=straight;FrontalCdA=aero==null?.75:aero[0];LateralCdA=aero==null?3.4:aero[1];VerticalCdA=aero==null?2:aero[2];PressureY=aero==null?.18:aero[3];PressureZ=aero==null?0:aero[4];if(rear!=null){RearCompression=rear[0];RearRebound=rear[1];RearDroop=rear[2];RearBump=rear[3];RearHalfTrack=rear.Length>4?rear[4]:0;}RearWheelDrive=rwd;HullOffsetZ=hullOffset;HullFriction=hullFriction;
        }
        public double DroopAt(int i) { return i>=2&&RearDroop>0?RearDroop:Droop; }
        public double BumpAt(int i) { return i>=2&&RearBump>0?RearBump:Bump; }
        public double RateAt(int i) { return i<2?FrontRate:RearRate; }
        public double TrackAt(int i) { return i>=2&&RearHalfTrack>0?RearHalfTrack:HalfTrack; }
    }
    // Exact donor tuning, metres / kilograms / seconds. Engineering estimates, not OEM data.
    public static class VehicleCatalog {
        static readonly VehicleTune[] data={
            new VehicleTune("safari","Safari",new[]{.49,.17,1.08,1.35,.28,.50,.38,.41},new[]{1072,.68,-.25,1.55,.65,3.50,22500,31500,2100,3500,.88,6200,1800,1900,700,.24,.30,.30}),
            new VehicleTune("buggy","Original buggy",new[]{.54,.20,1.50,1.35,.16,.68,.80,.41},new[]{780,.90,0,1.45,1.15,2.75,12000,14000,1400,2300,.90,5100,1050,1150,650,.50,.30,.30},false,new[]{.95,2.6,1.7,.20,0}),
            new VehicleTune("baja","Baja 427",new[]{.47,.187,1.025,1.59,.268,.52,.68,.40},new[]{2480,.75,.1272,1.72,1.05,4.25,52762.9,51138.8,3359,5598,.92,13400,5300,5600,2000,.20,.55,.30},true,new[]{1.30,4.7,2.8,.25,-.15}),
            new VehicleTune("switchback","Switchback 27",new[]{.31,.1175,.81,1.24,.260,.385,.30,.31},new[]{1080,.48,.2232,1.50,.75,4.20,41184.512,33192.131,2352.976,3764.762,1.12,7800,1450,1650,460,.18,.10,.08},true,new[]{.78,2.4,1.7,.16,-.10},new[]{1861.520,2867.747,.254,.394}),
            new VehicleTune("catrina","La Catrina",new[]{.2891,.0775,.765,1.5113,.19,.42,.18,.2891},new[]{1850,.62,-.18,2.02,.65,5.33,42000,36000,2400,3700,.95,8800,4100,4500,950,.19,.20,.18},true,new[]{.92,3.6,2.1,.19,-.10},new[]{2200,3300,.15,.42,.755},true,-.19,.30),
            new VehicleTune("media-luna","Media Luna",new[]{.34425,.1025,.73,1.4732,.24,.52,.10,.34425},new[]{1620,.55,-.08,1.88,.70,5.02,36000,32000,2100,3400,.95,7200,3600,4200,880,.20,.12,.10},true,new[]{.90,3.4,2,.18,-.06},new[]{2000,3200,.24,.50,.74},true,0,.32),
            new VehicleTune("nocturne","Nocturne",new[]{.348,.1125,.790,1.6002,.278,.418,.10,.348},new[]{2600,.64,-.03,1.99644,.66,5.49402,52000,50000,3600,5500,.95,10500,6300,7000,1450,.20,.16,.14},true,new[]{1.02,3.9,2.3,.20,-.08},new[]{3400,5200,.278,.418,.785},true,-.14681,.32)
        };
        public static VehicleTune[] All {get {return (VehicleTune[])data.Clone();}}
        internal static VehicleTune Get(int i) {return data[i];}
        public static int Count {get {return data.Length;}}
        public static int Index(string id) { for(int i=0;i<data.Length;i++)if(data[i].Id==id)return i;throw new ArgumentException("Unknown vehicle: "+id); }
    }
}
