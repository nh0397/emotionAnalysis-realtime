import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

const SimpleDotPlot = ({ data, dimensions, colorObjects }) => {
  // ALL HOOKS MUST BE AT THE TOP - NO EARLY RETURNS BEFORE THIS
  const svgRef = useRef(null);
  const [hoveredValue, setHoveredValue] = useState(null);
  const [range, setRange] = useState([0, 1]);
  const [filteredStates, setFilteredStates] = useState([]);
  const [orderOption, setOrderOption] = useState(null);

  const emotions = ['anger', 'fear', 'positive', 'sadness', 'surprise', 'joy', 'anticipation', 'trust', 'negative', 'disgust'];

  // useEffect MUST be after all useState hooks
  useEffect(() => {
    // Early return inside useEffect is OK
    if (!data || data.length === 0) return;

    const filteredData = getFilteredData();
    if (!filteredData.length) return;

    renderChart(filteredData);
  }, [data, filteredStates, orderOption, range, hoveredValue, emotions]);

  // Early return AFTER all hooks
  if (!data || data.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Loading emotion data...</p>
      </div>
    );
  }

  // Helper function to get filtered data
  const getFilteredData = () => {
    if (!data || data.length === 0) return [];

    // Filter data based on selected states
    let filteredData = [...data];
    if (filteredStates.length > 0) {
      filteredData = data.filter((obj) => filteredStates.includes(obj.state));
    }

    // Order data if option selected
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

    // Filter by emotion range
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

  // Helper function to render the chart
  const renderChart = (filteredData) => {
    const { width, height, margin } = dimensions;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    // Create main group
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

    const colorScale = d3.scaleOrdinal()
      .domain(emotions)
      .range(['#FF0000', '#FFA500', '#008000', '#0000FF', '#FFC0CB', '#FFD700', '#9400D3', '#00FFFF', '#A9A9A9', '#808000']);

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

    // Add dots for each emotion
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
        .style("cursor", "pointer")
        .on("mouseover", function(event, d) {
          // Create tooltip
          const tooltip = d3.select("body")
            .selectAll(".emotion-tooltip")
            .data([null])
            .join("div")
            .attr("class", "emotion-tooltip")
            .style("position", "absolute")
            .style("background", "rgba(0,0,0,0.8)")
            .style("color", "white")
            .style("padding", "8px")
            .style("border-radius", "4px")
            .style("font-size", "12px")
            .style("pointer-events", "none")
            .style("z-index", 1000);

          tooltip
            .style("opacity", 1)
            .html(`
              <strong>${d.state}</strong><br/>
              ${emotion}: ${d.value.toFixed(3)}
            `)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 10) + "px");
        })
        .on("mouseout", function() {
          d3.selectAll(".emotion-tooltip").style("opacity", 0);
        });
    });

    // Add axis labels
    g.append("text")
      .attr("x", width / 2)
      .attr("y", height + 50)
      .style("text-anchor", "middle")
      .style("font-size", "14px")
      .style("fill", "#333")
      .text("Emotion Scores");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -60)
      .attr("x", -height / 2)
      .style("text-anchor", "middle")
      .style("font-size", "14px")
      .style("fill", "#333")
      .text("States");

    // Add legend
    const legend = g.append("g")
      .attr("class", "legend")
      .attr("transform", `translate(${width - 150}, 20)`);

    emotions.forEach((emotion, i) => {
      const legendRow = legend.append("g")
        .attr("transform", `translate(0, ${i * 20})`);

      legendRow.append("circle")
        .attr("r", 4)
        .style("fill", colorScale(emotion))
        .style("cursor", "pointer")
        .on("mouseover", () => setHoveredValue(emotion))
        .on("mouseout", () => setHoveredValue(null));

      legendRow.append("text")
        .attr("x", 10)
        .attr("y", 4)
        .style("font-size", "12px")
        .style("fill", "#333")
        .style("cursor", "pointer")
        .text(emotion)
        .on("mouseover", () => setHoveredValue(emotion))
        .on("mouseout", () => setHoveredValue(null));
    });
  };

  // Get unique states for filter (after hooks)
  const allStates = data ? [...new Set(data.map(d => d.state))].sort() : [];
  const { width, height, margin } = dimensions;
  const svgWidth = width + margin.left + margin.right;
  const svgHeight = height + margin.top + margin.bottom;

  // Handler functions
  const handleStateFilter = (selectedStates) => {
    setFilteredStates(Array.from(selectedStates));
  };

  const handleOrderChange = (selectedOption) => {
    setOrderOption(selectedOption);
  };

  const handleRangeChange = (newRange) => {
    setRange(newRange);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      {/* Controls */}
      <div style={{ display: 'flex', gap: '20px', padding: '20px', background: '#f5f5f5', borderRadius: '8px' }}>
        
        {/* State Filter */}
        <div>
          <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
            Filter States:
          </label>
          <select 
            multiple 
            value={filteredStates}
            onChange={(e) => {
              const selected = Array.from(e.target.selectedOptions, option => option.value);
              handleStateFilter(selected);
            }}
            style={{ 
              height: '120px', 
              minWidth: '120px',
              padding: '4px'
            }}
          >
            {allStates.map(state => (
              <option key={state} value={state}>{state}</option>
            ))}
          </select>
          <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
            Hold Ctrl/Cmd to select multiple
          </div>
        </div>

        {/* Order By Filter */}
        <div>
          <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
            Order By Emotion:
          </label>
          <select 
            value={orderOption?.value || ''}
            onChange={(e) => {
              const emotion = e.target.value;
              if (emotion) {
                const colorObj = colorObjects.find(c => c.emotion === emotion);
                handleOrderChange(colorObj ? { value: emotion, label: emotion, color: colorObj.color } : null);
              } else {
                handleOrderChange(null);
              }
            }}
            style={{ padding: '8px', minWidth: '150px' }}
          >
            <option value="">Default Order</option>
            {emotions.map(emotion => (
              <option key={emotion} value={emotion}>{emotion}</option>
            ))}
          </select>
        </div>

        {/* Range Filter */}
        <div>
          <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
            Emotion Range:
          </label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div>
              <label style={{ fontSize: '12px' }}>Min: </label>
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.1" 
                value={range[0]}
                onChange={(e) => handleRangeChange([parseFloat(e.target.value), range[1]])}
                style={{ width: '100px' }}
              />
              <span style={{ fontSize: '12px', marginLeft: '8px' }}>{range[0]}</span>
            </div>
            <div>
              <label style={{ fontSize: '12px' }}>Max: </label>
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.1" 
                value={range[1]}
                onChange={(e) => handleRangeChange([range[0], parseFloat(e.target.value)])}
                style={{ width: '100px' }}
              />
              <span style={{ fontSize: '12px', marginLeft: '8px' }}>{range[1]}</span>
            </div>
          </div>
        </div>

        {/* Reset Button */}
        <div style={{ display: 'flex', alignItems: 'flex-end' }}>
          <button 
            onClick={() => {
              setFilteredStates([]);
              setOrderOption(null);
              setRange([0, 1]);
              setHoveredValue(null);
            }}
            style={{
              padding: '8px 16px',
              background: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Reset Filters
          </button>
        </div>
      </div>

      {/* Chart */}
      <div style={{ background: 'white', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <h3 style={{ margin: '0 0 20px 0', textAlign: 'center' }}>
          Real-time Emotion Analysis by State
        </h3>
        <svg ref={svgRef} width={svgWidth} height={svgHeight}></svg>
      </div>
    </div>
  );
};

export default SimpleDotPlot;
