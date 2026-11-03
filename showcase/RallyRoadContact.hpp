#pragma once
#include <algorithm>
#include <array>
#include <cmath>
#include <cstdint>
#include <optional>
#include <unordered_map>
#include <vector>

namespace rally {
// CPU height queries against the existing rendered road triangles. No second
// surface is generated: vertices and indices are the same arrays sent to GL.
class RoadContactSurface {
    struct Triangle {std::array<float,3> x,y,z;float inverseArea;};
    std::vector<Triangle> triangles_;
    std::unordered_map<std::uint64_t,std::vector<unsigned>> cells_;
    static constexpr float cellSize=2.f;
    static std::uint64_t key(int x,int z){return (static_cast<std::uint64_t>(static_cast<std::uint32_t>(x))<<32)|static_cast<std::uint32_t>(z);}
public:
    RoadContactSurface(const std::vector<float>& positions,const std::vector<unsigned>& indices){
        for(std::size_t n=0;n+2<indices.size();n+=3){Triangle t{};
            for(int j=0;j<3;++j){const auto i=3*indices[n+j];t.x[j]=positions.at(i);t.y[j]=positions.at(i+1);t.z[j]=positions.at(i+2);}
            const float area=(t.x[1]-t.x[0])*(t.z[2]-t.z[0])-(t.z[1]-t.z[0])*(t.x[2]-t.x[0]);if(std::abs(area)<1e-8f)continue;t.inverseArea=1/area;
            const auto index=static_cast<unsigned>(triangles_.size());triangles_.push_back(t);
            int x0=static_cast<int>(std::floor(*std::min_element(t.x.begin(),t.x.end())/cellSize)),x1=static_cast<int>(std::floor(*std::max_element(t.x.begin(),t.x.end())/cellSize));
            int z0=static_cast<int>(std::floor(*std::min_element(t.z.begin(),t.z.end())/cellSize)),z1=static_cast<int>(std::floor(*std::max_element(t.z.begin(),t.z.end())/cellSize));
            for(int x=x0;x<=x1;++x)for(int z=z0;z<=z1;++z)cells_[key(x,z)].push_back(index);
        }
    }
    std::optional<float> height(float x,float z)const {
        const auto found=cells_.find(key(static_cast<int>(std::floor(x/cellSize)),static_cast<int>(std::floor(z/cellSize))));if(found==cells_.end())return std::nullopt;
        for(const auto index:found->second){const auto& t=triangles_[index];
            const float u=((x-t.x[0])*(t.z[2]-t.z[0])-(z-t.z[0])*(t.x[2]-t.x[0]))*t.inverseArea;
            const float v=((t.x[1]-t.x[0])*(z-t.z[0])-(t.z[1]-t.z[0])*(x-t.x[0]))*t.inverseArea;
            if(u>=-.00001f&&v>=-.00001f&&u+v<=1.00001f)return t.y[0]+u*(t.y[1]-t.y[0])+v*(t.y[2]-t.y[0]);
        }return std::nullopt;
    }
    std::size_t triangleCount()const{return triangles_.size();}
};
}
