export const EARTH_TRAINING_SET = [
  {claim:"Methane is a greenhouse gas.",evidence:"Methane is classified as a greenhouse gas.",label:"SUPPORTED",category:"Climate"},
  {claim:"Solar panels can generate electricity from sunlight.",evidence:"Solar panels generate electricity by converting sunlight into electrical energy.",label:"SUPPORTED",category:"Energy"},
  {claim:"Wind turbines generate electricity from wind.",evidence:"Wind turbines use wind energy to generate electricity.",label:"SUPPORTED",category:"Energy"},
  {claim:"Trees can store carbon as they grow.",evidence:"Growing trees store carbon in their biomass.",label:"SUPPORTED",category:"Climate"},
  {claim:"Recycling aluminum can reduce demand for new aluminum ore.",evidence:"Recycling aluminum reduces the need to extract new aluminum ore.",label:"SUPPORTED",category:"Waste"},
  {claim:"Wetlands can provide habitat for wildlife.",evidence:"Wetlands provide habitat for many wildlife species.",label:"SUPPORTED",category:"Biodiversity"},
  {claim:"Drought can reduce available water supplies.",evidence:"Drought reduces water availability and can lower water supplies.",label:"SUPPORTED",category:"Water"},
  {claim:"Composting can divert food scraps from landfill.",evidence:"Composting diverts food scraps away from landfill disposal.",label:"SUPPORTED",category:"Waste"},
  {claim:"Public transit can move many people in one vehicle.",evidence:"Buses and trains can transport many passengers in a single vehicle.",label:"SUPPORTED",category:"Transport"},
  {claim:"Energy efficiency can reduce electricity use for the same service.",evidence:"Energy-efficient equipment can provide the same service while using less electricity.",label:"SUPPORTED",category:"Energy"},
  {claim:"Coral reefs provide habitat for marine life.",evidence:"Coral reefs are habitat for many marine organisms.",label:"SUPPORTED",category:"Biodiversity"},
  {claim:"Rain gardens can capture stormwater runoff.",evidence:"Rain gardens capture and absorb stormwater runoff.",label:"SUPPORTED",category:"Water"},

  {claim:"Wind turbines generate electricity by burning coal.",evidence:"Wind turbines do not burn coal; they generate electricity from wind.",label:"CONTRADICTED",category:"Energy"},
  {claim:"A drought means there is too much rainfall.",evidence:"A drought is a period of unusually low rainfall, not too much rainfall.",label:"CONTRADICTED",category:"Water"},
  {claim:"Methane is not a greenhouse gas.",evidence:"Methane is a greenhouse gas.",label:"CONTRADICTED",category:"Climate"},
  {claim:"Solar panels generate electricity only at night.",evidence:"Solar panels use sunlight, not darkness, to generate electricity.",label:"CONTRADICTED",category:"Energy"},
  {claim:"Recycling aluminum increases the need for new aluminum ore.",evidence:"Recycling aluminum decreases demand for new aluminum ore.",label:"CONTRADICTED",category:"Waste"},
  {claim:"Wetlands have no value as wildlife habitat.",evidence:"Wetlands provide wildlife habitat; the claim that they have no habitat value is false.",label:"CONTRADICTED",category:"Biodiversity"},
  {claim:"Composting sends every food scrap directly to landfill.",evidence:"Composting keeps organic material out of landfill rather than sending every scrap there.",label:"CONTRADICTED",category:"Waste"},
  {claim:"Energy efficiency always uses more electricity for the same service.",evidence:"Energy efficiency uses less electricity for the same service, not more.",label:"CONTRADICTED",category:"Energy"},
  {claim:"Rain gardens increase stormwater runoff by design.",evidence:"Rain gardens are designed to capture runoff, not increase it.",label:"CONTRADICTED",category:"Water"},
  {claim:"Coral reefs are not habitats for marine life.",evidence:"Coral reefs provide habitat for marine life.",label:"CONTRADICTED",category:"Biodiversity"},

  {claim:"One reusable bottle will completely stop ocean plastic pollution.",evidence:"Reusable bottles may reduce some single-use plastic waste.",label:"INSUFFICIENT",category:"Waste"},
  {claim:"Planting one tree guarantees a city will never flood.",evidence:"Trees may help reduce some stormwater runoff.",label:"INSUFFICIENT",category:"Climate"},
  {claim:"One solar panel will definitely eliminate a city's emissions.",evidence:"Solar panels can generate electricity without burning fuel at the point of generation.",label:"INSUFFICIENT",category:"Energy"},
  {claim:"A single bike lane proves all traffic pollution will disappear.",evidence:"Bike lanes may encourage some trips by bicycle.",label:"INSUFFICIENT",category:"Transport"},
  {claim:"Recycling one can guarantees a landfill will close.",evidence:"Recycling can divert some material from landfill.",label:"INSUFFICIENT",category:"Waste"},
  {claim:"One rainy day proves a drought is completely over.",evidence:"Rain may temporarily increase local water availability.",label:"INSUFFICIENT",category:"Water"},
  {claim:"A wildlife sighting proves an ecosystem is perfectly healthy.",evidence:"A wildlife sighting can provide information about one species at one time.",label:"INSUFFICIENT",category:"Biodiversity"},
  {claim:"Using public transit once guarantees a person's carbon footprint becomes zero.",evidence:"Public transit may reduce emissions for some trips compared with some car journeys.",label:"INSUFFICIENT",category:"Transport"},
  {claim:"A compost bin guarantees every environmental problem is solved.",evidence:"Composting can reduce some organic waste sent to landfill.",label:"INSUFFICIENT",category:"Waste"},
  {claim:"One efficient light bulb proves a building uses no electricity.",evidence:"An efficient bulb uses less electricity than a less efficient bulb for similar lighting.",label:"INSUFFICIENT",category:"Energy"}
];

export const EARTH_HOLDOUT_SET = [
  {claim:"Solar energy uses sunlight to generate electricity.",evidence:"Solar panels use sunlight to generate electricity.",label:"SUPPORTED",category:"Energy"},
  {claim:"A drought is caused by too much rainfall.",evidence:"Drought involves unusually low rainfall, not too much rainfall.",label:"CONTRADICTED",category:"Water"},
  {claim:"One recycled bottle guarantees plastic pollution will completely disappear.",evidence:"Recycling may reduce some plastic waste.",label:"INSUFFICIENT",category:"Waste"},
  {claim:"Wetlands can support wildlife.",evidence:"Wetlands provide habitat that supports wildlife.",label:"SUPPORTED",category:"Biodiversity"},
  {claim:"Wind turbines burn coal to make electricity.",evidence:"Wind turbines do not burn coal; they use wind to generate electricity.",label:"CONTRADICTED",category:"Energy"},
  {claim:"Planting one tree guarantees global warming will stop.",evidence:"Trees can store carbon as they grow.",label:"INSUFFICIENT",category:"Climate"},
  {claim:"Composting can reduce food waste sent to landfill.",evidence:"Composting diverts food scraps from landfill.",label:"SUPPORTED",category:"Waste"},
  {claim:"Energy efficiency always requires more electricity.",evidence:"Energy efficiency uses less electricity for the same service, not more.",label:"CONTRADICTED",category:"Energy"},
  {claim:"One rain garden proves a city will never flood.",evidence:"Rain gardens may capture some stormwater runoff.",label:"INSUFFICIENT",category:"Water"},
  {claim:"Coral reefs provide habitat for marine organisms.",evidence:"Coral reefs are habitat for many marine organisms.",label:"SUPPORTED",category:"Biodiversity"}
];

export const EARTH_CATEGORIES = ["Climate","Energy","Water","Waste","Biodiversity","Transport","General"];
