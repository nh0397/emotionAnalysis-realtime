import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import * as d3 from 'd3';
import EmotionCircles from './EmotionCircles';
import StateLines from './StateLines';
import ColorLegend from './Legend';
import TwoWaySlider from './TwoWaySlider';
import StateFilter from './StateFilter';
import DataOrderFilter from './DataOrderFilter';
import EmotionTornadoChart from '../views/EmotionTornadoChart';
import TimeSeriesChart from './TimeSeriesChart';
import Xaxis from './Xaxis';
import Yaxis from './Yaxis';

const SimpleDotPlot = ({ data, dimensions, colorObjects, timeSeriesData }) => {
  // ALL HOOKS MUST BE AT THE TOP - NO EARLY RETURNS BEFORE THIS
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [hoveredValue, setHoveredValue] = useState(null);
  const [range, setRange] = useState([0, 1]);
  const [tempRange, setTempRange] = useState([0, 1]);
  const [filteredStates, setFilteredStates] = useState([]);
  const [orderOption, setOrderOption] = useState(null);
  const [selectedLines, setSelectedLines] = useState([]);
  const [selectedState, setSelectedState] = useState("");
  const [filteredDataTimeSeries, setFilteredDataTimeSeries] = useState("");

  const emotions = ['anger', 'fear', 'positive', 'sadness', 'surprise', 'joy', 'anticipation', 'trust', 'negative', 'disgust'];

  // Memoized values
  const { width, height, margin } = dimensions;
  const svgWidth = width + margin.left + margin.right;
  const svgHeight = height + margin.top + margin.bottom;
  const middleX = svgWidth / 2 - 500;
  const middleY = svgHeight - dimensions.height;

  // Memoized data processing
  const processedData = useMemo(() => {
    if (!data || data.length === 0) return [];

    let processed = [...data];
    
    // Filter by states
    if (filteredStates.length > 0) {
      processed = processed.filter((obj) => filteredStates.includes(obj.state));
    }

    // Order data
    if (orderOption) {
      processed.sort((a, b) =>
        d3.ascending(
          parseFloat(a[orderOption.value]),
          parseFloat(b[orderOption.value])
        )
      );
    } else {
      processed.sort((a, b) => a.state.localeCompare(b.state));
    }

    // Filter by emotion range
    if (range[0] !== 0 || range[1] !== 1) {
      processed = processed.map((obj) => {
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

    return processed;
  }, [data, filteredStates, orderOption, range]);

  // Memoized filtered data for hover effects
  const hoveredData = useMemo(() => {
    if (!hoveredValue || !processedData.length) return processedData;

    return processedData.map((obj) => {
      const filteredObj = {};
      for (const [key, value] of Object.entries(obj)) {
        if (key === "state" || key === hoveredValue.emotion) {
          filteredObj[key] = value;
        }
      }
      return filteredObj;
    });
  }, [processedData, hoveredValue]);

  // Memoized scales
  const scales = useMemo(() => {
    const xScale = d3.scaleLinear()
      .domain([0, 1])
      .range([0, width])
      .nice();

    const yScale = d3.scaleBand()
      .range([0, height])
      .domain(processedData.map((d) => d.state))
      .padding(1);

    const colorScale = d3.scaleOrdinal()
      .domain(emotions)
      .range(['#FF0000', '#FFA500', '#008000', '#0000FF', '#FFC0CB', '#FFD700', '#9400D3', '#00FFFF', '#A9A9A9', '#808000']);

    return { xScale, yScale, colorScale };
  }, [processedData, width, height]);

  // Memoized order options
  const orderOptions = useMemo(() => {
    return colorObjects.map((emotionColor) => ({
      value: emotionColor.emotion,
      label: emotionColor.emotion,
      color: emotionColor.color,
    }));
  }, [colorObjects]);

  // Memoized unique states
  const allStates = useMemo(() => {
    return data ? [...new Set(data.map(d => d.state))].sort() : [];
  }, [data]);

  // Event handlers
  const handleStateFilter = useCallback((selectedStates) => {
    setFilteredStates(Array.from(selectedStates));
  }, []);

  const handleOrderChange = useCallback((selectedOption) => {
    setOrderOption(selectedOption);
  }, []);

  const handleRangeChange = useCallback((newRange) => {
    setRange(newRange);
  }, []);

  const handleSliderChange = useCallback((index, value) => {
    if (index === 0) {
      setTempRange((prev) => [value, prev[1]]);
    } else {
      setTempRange((prev) => [prev[0], value]);
    }
  }, []);

  const handleSliderEnd = useCallback((index, value) => {
    if (index === 0) {
      setRange((prev) => [value, prev[1]]);
      setTempRange((prev) => [value, prev[1]]);
    } else {
      setRange((prev) => [prev[0], value]);
      setTempRange((prev) => [prev[0], value]);
    }
  }, []);

  const onStateSelection = useCallback((selectedData) => {
    const selectedOptions = Array.from(selectedData);
    setFilteredStates(selectedOptions);
  }, []);

  const onDataOrderSelection = useCallback((selectedData) => {
    setOrderOption(selectedData);
  }, []);

  const handleTickClick = useCallback((state) => {
    console.log("tick clicked", state);
    setSelectedState(state);
    const filteredData = timeSeriesData.filter((d) => d.state === state);
    setFilteredDataTimeSeries(filteredData);
  }, [timeSeriesData]);

  const resetFilters = useCallback(() => {
    setFilteredStates([]);
    setOrderOption(null);
    setRange([0, 1]);
    setTempRange([0, 1]);
    setHoveredValue(null);
    setSelectedLines([]);
  }, []);

  // Click outside handler
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setSelectedLines([]);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Main rendering effect
  useEffect(() => {
    if (!svgRef.current || !processedData.length) return;
    
    renderChart();
  }, [processedData, hoveredValue, selectedLines, scales]);

  // Cleanup tooltips on unmount
  useEffect(() => {
    return () => {
      d3.selectAll(".emotion-tooltip").remove();
    };
  }, []);

  // D3 chart rendering function
  const renderChart = useCallback(() => {
    const container = d3.select(svgRef.current);
    container.selectAll("*").remove();

    const svg = container.append("svg")
      .attr("width", svgWidth)
      .attr("height", svgHeight);

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    const { xScale, yScale, colorScale } = scales;

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
      .style("text-anchor", "end")
      .style("font-size", "12px")
      .style("fill", "#333")
      .style("cursor", "pointer")
      .on("click", function(event, d) {
        handleTickClick(d);
      });

    // Add state lines connecting emotion dots
    processedData.forEach((stateData) => {
      const stateY = yScale(stateData.state);
      
      // Get emotion values for this state
      const emotionValues = emotions
        .filter(emotion => stateData[emotion] !== undefined && stateData[emotion] !== null)
        .map(emotion => ({
          emotion,
          value: parseFloat(stateData[emotion]) || 0,
          x: xScale(parseFloat(stateData[emotion]) || 0),
          y: stateY
        }))
        .filter(d => !isNaN(d.value));

      if (emotionValues.length > 1) {
        const line = d3.line()
          .x(d => d.x)
          .y(d => d.y);

        g.append("path")
          .datum(emotionValues)
          .attr("class", "state-line")
          .attr("d", line)
          .attr("stroke", selectedLines.includes(stateData.state) ? "#007bff" : "#ddd")
          .attr("stroke-width", selectedLines.includes(stateData.state) ? 2 : 1)
          .attr("fill", "none")
          .style("cursor", "pointer")
          .on("click", () => {
            if (selectedLines.length < 2) {
              setSelectedLines(prev => [...prev, stateData.state]);
            } else {
              setSelectedLines([stateData.state]);
            }
          });
      }
    });

    // Add dots for each emotion
    emotions.forEach((emotion) => {
      const emotionData = processedData
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
        .style("opacity", hoveredValue && hoveredValue.emotion !== emotion ? 0.3 : 1)
        .style("stroke", hoveredValue && hoveredValue.emotion === emotion ? "#000" : "none")
        .style("stroke-width", hoveredValue && hoveredValue.emotion === emotion ? 2 : 0)
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

    // Add legend
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
        .style("stroke", hoveredValue && hoveredValue.emotion === emotion ? "#000" : "none")
        .style("stroke-width", hoveredValue && hoveredValue.emotion === emotion ? 2 : 0)
        .style("opacity", hoveredValue && hoveredValue.emotion !== emotion ? 0.5 : 1);

      legendRow.append("text")
        .attr("x", 15)
        .attr("y", 5)
        .style("font-size", "13px")
        .style("fill", "#333")
        .style("font-weight", hoveredValue && hoveredValue.emotion === emotion ? "bold" : "normal")
        .text(emotion.charAt(0).toUpperCase() + emotion.slice(1));

      legendRow
        .on("mouseover", () => setHoveredValue({ emotion }))
        .on("mouseout", () => setHoveredValue(null));
    });

    // Add axis labels
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
      .attr("y", -60)
      .attr("x", -height / 2)
      .style("text-anchor", "middle")
      .style("font-size", "14px")
      .style("fill", "#333")
      .style("font-weight", "bold")
      .text("States");

    // Add tornado chart if two states are selected
    if (selectedLines.length === 2) {
      const state1Data = processedData.find(d => d.state === selectedLines[0]);
      const state2Data = processedData.find(d => d.state === selectedLines[1]);
      
      if (state1Data && state2Data) {
        const tornadoX = width / 2 - 150;
        const tornadoY = 50;
        
        const tornadoG = g.append("g")
          .attr("transform", `translate(${tornadoX}, ${tornadoY})`);
        
        tornadoG.append("rect")
          .attr("x", 0)
          .attr("y", 0)
          .attr("width", 300)
          .attr("height", 200)
          .style("fill", "rgba(255,255,255,0.9)")
          .style("stroke", "#333")
          .style("stroke-width", 1);
        
        tornadoG.append("text")
          .attr("x", 150)
          .attr("y", 20)
          .style("text-anchor", "middle")
          .style("font-size", "14px")
          .style("font-weight", "bold")
          .text(`${state1Data.state} vs ${state2Data.state}`);
      }
    }
  }, [processedData, hoveredValue, selectedLines, scales, svgWidth, svgHeight, margin, width, height, emotions, handleTickClick, setSelectedLines, setHoveredValue]);

  // Early return AFTER all hooks
  if (!data || data.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <p>Loading emotion data...</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} style={{ display: 'flex', gap: '20px', minHeight: '800px', width: '100%' }}>
      
      {/* Left Column - Graph (75% width) */}
      <div style={{ flex: '3', display: 'flex', flexDirection: 'column' }}>
        
        {/* Main Dot Plot */}
        {!selectedState && (
          <div style={{ 
            background: 'white', 
            padding: '20px', 
            borderRadius: '8px', 
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            flex: '1',
            display: 'flex',
            flexDirection: 'column'
          }}>
            {/* Chart Container */}
            <div 
              ref={svgRef} 
              style={{ 
                width: svgWidth, 
                height: svgHeight, 
                position: 'relative',
                border: '1px solid #e0e0e0',
                borderRadius: '4px'
              }}
            >
              {/* Main Chart SVG - will be populated by D3 */}
            </div>
          </div>
        )}

        {/* Time Series Chart */}
        {selectedState && timeSeriesData && (
          <div style={{ 
            background: 'white', 
            padding: '20px', 
            borderRadius: '8px', 
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            flex: '1'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h4 style={{ margin: 0 }}>Time Series Analysis for {selectedState}</h4>
              <button 
                onClick={() => setSelectedState("")}
                style={{
                  padding: '8px 16px',
                  background: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                ← Back to Dot Plot
              </button>
            </div>
            <TimeSeriesChart
              dimensions={{
                width: Math.min(800, window.innerWidth - 100),
                height: 400,
                margin: { top: 20, right: 30, bottom: 60, left: 60 }
              }}
              data={timeSeriesData}
              states={allStates}
              selectedState={selectedState}
            />
          </div>
        )}

        {/* Color Legend */}
        <div style={{ 
          marginTop: '20px', 
          padding: '20px', 
          background: '#f8f9fa', 
          borderRadius: '8px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center'
        }}>
          <h4 style={{ margin: '0 0 15px 0' }}>Emotion Colors:</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '15px', justifyContent: 'center' }}>
            {emotions.map((emotion, i) => (
              <div 
                key={emotion}
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  cursor: 'pointer',
                  opacity: hoveredValue === emotion ? 1 : 0.7
                }}
                onMouseEnter={() => setHoveredValue({ emotion })}
                onMouseLeave={() => setHoveredValue(null)}
              >
                <div 
                  style={{
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    backgroundColor: ['#FF0000', '#FFA500', '#008000', '#0000FF', '#FFC0CB', '#FFD700', '#9400D3', '#00FFFF', '#A9A9A9', '#808000'][i]
                  }}
                />
                <span style={{ fontSize: '14px' }}>{emotion}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Column - Filters (25% width) */}
      <div style={{ flex: '1', display: 'flex', flexDirection: 'column', gap: '15px' }}>
        
        {/* State Filter */}
        <div style={{ 
          background: '#f5f5f5', 
          padding: '20px', 
          borderRadius: '8px',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <label style={{ fontWeight: 'bold', marginBottom: '12px', display: 'block' }}>
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
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid #ddd'
            }}
          >
            {allStates.map(state => (
              <option key={state} value={state}>{state}</option>
            ))}
          </select>
          <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
            Hold Ctrl/Cmd to select multiple
          </div>
        </div>

        {/* Order By Filter */}
        <div style={{ 
          background: '#f5f5f5', 
          padding: '20px', 
          borderRadius: '8px',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <label style={{ fontWeight: 'bold', marginBottom: '12px', display: 'block' }}>
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
            style={{ 
              padding: '10px', 
              borderRadius: '4px',
              border: '1px solid #ddd',
              fontSize: '14px'
            }}
          >
            <option value="">Default Order</option>
            {emotions.map(emotion => (
              <option key={emotion} value={emotion}>{emotion}</option>
            ))}
          </select>
        </div>

        {/* Range Filter */}
        <div style={{ 
          background: '#f5f5f5', 
          padding: '20px', 
          borderRadius: '8px',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <label style={{ fontWeight: 'bold', marginBottom: '12px', display: 'block' }}>
            Emotion Range (0-1):
          </label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <div>
              <label style={{ fontSize: '14px', display: 'block', marginBottom: '8px' }}>Min: {tempRange[0]}</label>
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.01" 
                value={tempRange[0]}
                onChange={(e) => handleSliderChange(0, parseFloat(e.target.value))}
                onMouseUp={(e) => handleSliderEnd(0, parseFloat(e.target.value))}
                onTouchEnd={(e) => handleSliderEnd(0, parseFloat(e.target.value))}
                style={{ 
                  width: '100%',
                  height: '6px',
                  borderRadius: '3px',
                  background: '#ddd',
                  outline: 'none'
                }}
              />
            </div>
            <div>
              <label style={{ fontSize: '14px', display: 'block', marginBottom: '8px' }}>Max: {tempRange[1]}</label>
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.01" 
                value={tempRange[1]}
                onChange={(e) => handleSliderChange(1, parseFloat(e.target.value))}
                onMouseUp={(e) => handleSliderEnd(1, parseFloat(e.target.value))}
                onTouchEnd={(e) => handleSliderEnd(1, parseFloat(e.target.value))}
                style={{ 
                  width: '100%',
                  height: '6px',
                  borderRadius: '3px',
                  background: '#ddd',
                  outline: 'none'
                }}
              />
            </div>
          </div>
        </div>

        {/* Reset Button */}
        <div style={{ 
          background: '#f5f5f5', 
          padding: '20px', 
          borderRadius: '8px',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <button 
            onClick={resetFilters}
            style={{
              padding: '12px 20px',
              background: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => e.target.style.background = '#0056b3'}
            onMouseLeave={(e) => e.target.style.background = '#007bff'}
          >
            Reset All Filters
          </button>
        </div>
      </div>
    </div>
  );
};

export default SimpleDotPlot;
