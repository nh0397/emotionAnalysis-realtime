import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import './EnhancedDotPlot.css';

const EnhancedDotPlot = ({ data, dimensions, colorObjects }) => {
  // ALL HOOKS MUST BE AT THE TOP
  const svgRef = useRef(null);
  const [hoveredValue, setHoveredValue] = useState(null);
  const [range, setRange] = useState([0, 1]);
  const [filteredStates, setFilteredStates] = useState([]);
  const [orderOption, setOrderOption] = useState(null);

  const emotions = ['anger', 'fear', 'positive', 'sadness', 'surprise', 'joy', 'anticipation', 'trust', 'negative', 'disgust'];

  // Color scale matching original
  const colorScale = d3.scaleOrdinal()
    .domain(emotions)
    .range(['#FF0000', '#FFA500', '#008000', '#0000FF', '#FFC0CB', '#FFD700', '#9400D3', '#00FFFF', '#A9A9A9', '#808000']);

  // useEffect for rendering
  useEffect(() => {
    if (!data || data.length === 0) return;
    const filteredData = getFilteredData();
    if (!filteredData.length) return;
    renderChart(filteredData);
  }, [data, filteredStates, orderOption, range, hoveredValue]);

  // Early return AFTER all hooks
  if (!data || data.length === 0) {
    return (
      <div className="loading-container">
        <p>Loading emotion data...</p>
      </div>
    );
  }

  const getFilteredData = () => {
    if (!data || data.length === 0) return [];

    let filteredData = [...data];
    if (filteredStates.length > 0) {
      filteredData = data.filter((obj) => filteredStates.includes(obj.state));
    }

    if (orderOption) {
      filteredData.sort((a, b) =>
        d3.ascending(
          parseFloat(a[orderOption.value]),
          parseFloat(b[orderOption.value])
        )
      );
    } else {
      filteredData.sort((a, b) => a.state.localeCompare(b.state));
    }

    if (range[0] !== 0 || range[1] !== 1) {
      filteredData = filteredData.map((obj) => {
        const filteredObj = {};
        for (const [key, value] of Object.entries(obj)) {
          if (key === "state") {
            filteredObj[key] = value;
          } else if (emotions.includes(key)) {
            const val = parseFloat(value);
            if (val >= range[0] && val <= range[1]) {
              filteredObj[key] = value;
            }
          }
        }
        return filteredObj;
      });
    }

    return filteredData;
  };

  const renderChart = (filteredData) => {
    const { width, height, margin } = dimensions;
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Main chart group
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Scales
    const xScale = d3.scaleLinear()
      .domain([0, 0.6])
      .range([0, width])
      .nice();

    const yScale = d3.scaleBand()
      .range([0, height])
      .domain(filteredData.map((d) => d.state))
      .padding(1);

    // Add axes
    g.append("g")
      .attr("class", "x-axis")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(xScale))
      .selectAll("text")
      .style("font-size", "12px")
      .style("fill", "#333");

    g.append("g")
      .attr("class", "y-axis")
      .call(d3.axisLeft(yScale))
      .selectAll("text")
      .style("font-size", "12px")
      .style("fill", "#333")
      .style("cursor", "pointer");

    // Add emotion dots
    emotions.forEach((emotion) => {
      const emotionData = filteredData
        .filter(d => d[emotion] !== undefined && d[emotion] !== null)
        .map(d => ({
          state: d.state,
          value: parseFloat(d[emotion]) || 0,
          emotion: emotion
        }));

      g.selectAll(`.dot-${emotion}`)
        .data(emotionData)
        .enter()
        .append("circle")
        .attr("class", `dot-${emotion}`)
        .attr("cx", d => xScale(d.value))
        .attr("cy", d => yScale(d.state))
        .attr("r", 4)
        .style("fill", colorScale(emotion))
        .style("opacity", hoveredValue === emotion ? 1 : 0.7)
        .style("stroke", hoveredValue === emotion ? "#000" : "none")
        .style("stroke-width", hoveredValue === emotion ? 2 : 0)
        .style("cursor", "pointer")
        .on("mouseover", function(event, d) {
          d3.select("body")
            .selectAll(".emotion-tooltip")
            .data([null])
            .join("div")
            .attr("class", "emotion-tooltip")
            .style("position", "absolute")
            .style("background", "rgba(0,0,0,0.9)")
            .style("color", "white")
            .style("padding", "12px")
            .style("border-radius", "8px")
            .style("font-size", "13px")
            .style("pointer-events", "none")
            .style("z-index", 1000)
            .style("box-shadow", "0 4px 8px rgba(0,0,0,0.3)")
            .style("opacity", 1)
            .html(`
              <strong>${d.state}</strong><br/>
              <span style="color: ${colorScale(emotion)}">${emotion}</span>: ${d.value.toFixed(3)}
            `)
            .style("left", (event.pageX + 15) + "px")
            .style("top", (event.pageY - 10) + "px");
        })
        .on("mouseout", function() {
          d3.selectAll(".emotion-tooltip").style("opacity", 0);
        });
    });

    // Axis labels
    g.append("text")
      .attr("x", width / 2)
      .attr("y", height + 50)
      .style("text-anchor", "middle")
      .style("font-size", "14px")
      .style("fill", "#333")
      .style("font-weight", "bold")
      .text("Emotion Scores");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -70)
      .attr("x", -height / 2)
      .style("text-anchor", "middle")
      .style("font-size", "14px")
      .style("fill", "#333")
      .style("font-weight", "bold")
      .text("States");

    // Enhanced Legend
    const legend = g.append("g")
      .attr("class", "legend")
      .attr("transform", `translate(${width - 140}, 20)`);

    emotions.forEach((emotion, i) => {
      const legendRow = legend.append("g")
        .attr("transform", `translate(0, ${i * 25})`)
        .style("cursor", "pointer");

      legendRow.append("circle")
        .attr("r", 6)
        .style("fill", colorScale(emotion))
        .style("stroke", hoveredValue === emotion ? "#000" : "none")
        .style("stroke-width", hoveredValue === emotion ? 2 : 0)
        .style("opacity", hoveredValue === emotion ? 1 : 0.8);

      legendRow.append("text")
        .attr("x", 15)
        .attr("y", 5)
        .style("font-size", "13px")
        .style("fill", "#333")
        .style("font-weight", hoveredValue === emotion ? "bold" : "normal")
        .text(emotion.charAt(0).toUpperCase() + emotion.slice(1));

      legendRow
        .on("mouseover", () => setHoveredValue(emotion))
        .on("mouseout", () => setHoveredValue(null));
    });
  };

  // Helper functions
  const allStates = data ? [...new Set(data.map(d => d.state))].sort() : [];
  const { width, height, margin } = dimensions;
  const svgWidth = width + margin.left + margin.right;
  const svgHeight = height + margin.top + margin.bottom;

  const handleStateFilter = (selectedStates) => {
    setFilteredStates(Array.from(selectedStates));
  };

  const handleOrderChange = (emotion) => {
    setOrderOption(emotion ? { value: emotion, label: emotion } : null);
  };

  const handleRangeChange = (newRange) => {
    setRange(newRange);
  };

  return (
    <div className="enhanced-dotplot-container">
      {/* Title */}
      <div className="chart-header">
        <h2>Real-time Emotion Analysis by State</h2>
        <p>Interactive visualization of emotion scores aggregated by state</p>
      </div>

      {/* Main SVG with embedded filters */}
      <svg ref={svgRef} width={svgWidth} height={svgHeight} className="main-chart">
        
        {/* State Filter - Top Right */}
        <foreignObject x={svgWidth - 360} y={20} width="340" height="280">
          <div className="state-filter-container">
            <h4>Filter by States</h4>
            <select 
              multiple 
              value={filteredStates}
              onChange={(e) => handleStateFilter([...e.target.selectedOptions].map(o => o.value))}
              className="state-multiselect"
            >
              {allStates.map(state => (
                <option key={state} value={state}>{state}</option>
              ))}
            </select>
            <div className="filter-info">
              {filteredStates.length > 0 ? 
                `${filteredStates.length} state(s) selected` : 
                "All states shown"
              }
            </div>
          </div>
        </foreignObject>

        {/* Order Filter - Top Center */}
        <foreignObject x={svgWidth - 720} y={20} width="340" height="140">
          <div className="order-filter-container">
            <h4>Order by Emotion</h4>
            <select 
              value={orderOption?.value || ''}
              onChange={(e) => handleOrderChange(e.target.value)}
              className="emotion-select"
            >
              <option value="">Default (Alphabetical)</option>
              {emotions.map(emotion => (
                <option key={emotion} value={emotion}>
                  {emotion.charAt(0).toUpperCase() + emotion.slice(1)}
                </option>
              ))}
            </select>
          </div>
        </foreignObject>

        {/* Range Slider - Bottom */}
        <foreignObject x={margin.left} y={svgHeight - 120} width={width} height="100">
          <div className="range-slider-container">
            <h4>Emotion Score Range: {range[0].toFixed(2)} - {range[1].toFixed(2)}</h4>
            <div className="dual-range-slider">
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.01" 
                value={range[0]}
                onChange={(e) => handleRangeChange([parseFloat(e.target.value), range[1]])}
                className="range-input range-input-lower"
              />
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.01" 
                value={range[1]}
                onChange={(e) => handleRangeChange([range[0], parseFloat(e.target.value)])}
                className="range-input range-input-upper"
              />
              <div className="range-labels">
                <span>0.0</span>
                <span>1.0</span>
              </div>
            </div>
          </div>
        </foreignObject>

        {/* Reset Button */}
        <foreignObject x={svgWidth - 720} y={180} width="120" height="60">
          <button 
            onClick={() => {
              setFilteredStates([]);
              setOrderOption(null);
              setRange([0, 1]);
              setHoveredValue(null);
            }}
            className="reset-button"
          >
            Reset Filters
          </button>
        </foreignObject>

      </svg>
    </div>
  );
};

export default EnhancedDotPlot;
