import React, { useRef, useState, useEffect, useMemo, useCallback } from 'react';
import * as d3 from 'd3';
import ColorLegend from './Legend';
import Xaxis from './Xaxis';
import Yaxis from './Yaxis';
import EmotionCircles from './EmotionCircles';
import StateLines from './StateLines';
import TwoWaySlider from './TwoWaySlider';
import StateFilter from './StateFilter';
import DataOrderFilter from './DataOrderFilter';

const OriginalDotPlot = ({ data, dimensions, colorObjects }) => {
  // ALL HOOKS MUST BE AT THE TOP
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [hoveredValue, setHoveredValue] = useState(null);
  const [range, setRange] = useState([0, 1]);
  const [tempRange, setTempRange] = useState([0, 1]);
  const [filteredStates, setFilteredStates] = useState([]);
  const [orderOption, setOrderOption] = useState(null);
  const [selectedLines, setSelectedLines] = useState([]);

  // Early return AFTER all hooks
  if (!data || data.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: 'white' }}>
        <p>Loading emotion data...</p>
      </div>
    );
  }

  // MEMOIZE expensive calculations to prevent re-rendering
  const { width, height, margin } = dimensions;
  const svgWidth = width + margin.left + margin.right;
  const svgHeight = height + margin.top + margin.bottom;
  
  const fadeOpacity = 0.3;

  // MEMOIZE filtered and sorted data
  const processedData = useMemo(() => {
    let filteredData = [...data];
    
    // Filter by selected states
    if (filteredStates.length !== 0) {
      filteredData = data.filter((obj) => filteredStates.includes(obj.state));
    }

    // Order data by selected emotion
    if (orderOption) {
      filteredData.sort((a, b) => 
        d3.ascending(parseFloat(a[orderOption.value]), parseFloat(b[orderOption.value]))
      );
    } else {
      filteredData.sort((a, b) => a.state.localeCompare(b.state));
    }

    return filteredData;
  }, [data, filteredStates, orderOption]);

  // MEMOIZE order options
  const orderOptions = useMemo(() => 
    colorObjects.map((emotionColor) => ({
      value: emotionColor.emotion,
      label: emotionColor.emotion,
      color: emotionColor.color,
    })), [colorObjects]
  );

  // MEMOIZE scales
  const { xScale, yScale } = useMemo(() => {
    const xScale = d3.scaleLinear()
      .domain([0, 0.6])
      .range([0, width])
      .nice();

    const yScale = d3.scaleBand()
      .range([0, height])
      .domain(processedData.map((d) => d.state))
      .padding(1);

    return { xScale, yScale };
  }, [width, height, processedData]);

  // MEMOIZED event handlers to prevent re-rendering
  const onDataOrderSelection = useCallback((selectedData) => {
    setOrderOption(selectedData);
  }, []);

  const handleSliderChange = useCallback((index, value) => {
    if (index === 0) {
      setTempRange((prevTempRange) => [value, prevTempRange[1]]);
    } else {
      setTempRange((prevTempRange) => [prevTempRange[0], value]);
    }
  }, []);

  const handleSliderEnd = useCallback((index, value) => {
    if (index === 0) {
      setRange((prevRange) => [value, prevRange[1]]);
    } else {
      setRange((prevRange) => [prevRange[0], value]);
    }
  }, []);

  const onStateSelection = useCallback((selectedData) => {
    if (selectedData && selectedData.length > 0) {
      setFilteredStates(selectedData);
    } else {
      setFilteredStates([]);
    }
  }, []);

  const handleTickClick = useCallback((state) => {
    setFilteredStates(prev => {
      if (prev.includes(state)) {
        return prev.filter(s => s !== state);
      } else {
        return [...prev, state];
      }
    });
  }, []);

  // MEMOIZE all states list
  const allStates = useMemo(() => {
    return [...new Set(data.map(d => d.state))].sort();
  }, [data]);

  // MEMOIZE range-filtered data
  const rangeFilteredData = useMemo(() => {
    if (range[0] === 0 && range[1] === 1) {
      return processedData;
    }
    
    return processedData.map((obj) => {
      const filteredObj = {};
      for (const [key, value] of Object.entries(obj)) {
        if (key === "state") {
          filteredObj[key] = value;
        } else if (colorObjects.some(c => c.emotion === key)) {
          const val = parseFloat(value);
          if (val >= range[0] && val <= range[1]) {
            filteredObj[key] = value;
          }
        } else {
          filteredObj[key] = value; // Keep non-emotion fields
        }
      }
      return filteredObj;
    });
  }, [processedData, range, colorObjects]);

  return (
    <div ref={containerRef} style={{ position: 'relative', width: '100%', height: '100%' }}>
      <svg ref={svgRef} width={svgWidth} height={svgHeight}>
        
        {/* Tooltip */}
        <g className="tooltip" style={{ opacity: 0, pointerEvents: 'none' }}>
          <rect 
            width="160" 
            height="80" 
            fill="rgba(0,0,0,0.9)" 
            stroke="rgba(255,255,255,0.2)" 
            strokeWidth="1" 
            rx="8" 
          />
          <text className="tooltip-text" x="10" y="20" fill="white" fontSize="12" />
        </g>

        {/* Main Chart Group */}
        <g transform={`translate(${margin.left}, ${margin.top})`}>
          
          {/* X Axis */}
          <Xaxis 
            scale={xScale} 
            transform={`translate(0, ${height})`} 
            tickSize={height}
          />
          
          {/* Y Axis */}
          <Yaxis 
            scale={yScale} 
            transform="translate(0, 0)" 
            handleTickClick={handleTickClick}
          />
          
          {/* State Lines - MISSING FROM SIMPLE VERSION */}
          <StateLines
            data={rangeFilteredData}
            xScale={xScale}
            yScale={yScale}
            transform="translate(0, 0)"
            selectedStates={filteredStates}
            selectedLines={selectedLines}
            setSelectedLines={setSelectedLines}
          />
          
          {/* Emotion Circles */}
          <EmotionCircles
            colorObjects={colorObjects}
            data={rangeFilteredData}
            xScale={xScale}
            yScale={yScale}
            transform="translate(0, 0)"
            opacity={hoveredValue ? fadeOpacity : 1}
          />
          
          {/* Legend */}
          <ColorLegend
            colorScale={colorObjects}
            onHover={setHoveredValue}
            hoveredValue={hoveredValue}
            fadeOpacity={fadeOpacity}
            transform={`translate(${width - 140}, 20)`}
          />
          
          {/* Axis Labels */}
          <text
            x={width / 2}
            y={height + 50}
            textAnchor="middle"
            fontSize="14"
            fill="white"
            fontWeight="bold"
          >
            Emotion Scores
          </text>
          
          <text
            transform="rotate(-90)"
            y={-70}
            x={-height / 2}
            textAnchor="middle"
            fontSize="14"
            fill="white"
            fontWeight="bold"
          >
            States
          </text>
        </g>

        {/* State Filter - Positioned outside main chart */}
        <foreignObject x={svgWidth - 280} y={20} width="260" height="200">
          <div style={{ 
            background: 'rgba(0,0,0,0.8)', 
            padding: '10px', 
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.2)'
          }}>
            <h4 style={{ color: 'white', margin: '0 0 10px 0', fontSize: '12px' }}>Filter States</h4>
            <select 
              multiple 
              value={filteredStates}
              onChange={(e) => onStateSelection([...e.target.selectedOptions].map(o => o.value))}
              style={{
                width: '100%',
                height: '120px',
                background: 'rgba(255,255,255,0.1)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)',
                borderRadius: '4px',
                fontSize: '11px'
              }}
            >
              {allStates.map(state => (
                <option key={state} value={state} style={{padding: '2px'}}>{state}</option>
              ))}
            </select>
            <div style={{color: 'white', fontSize: '10px', marginTop: '5px'}}>
              {filteredStates.length > 0 ? `${filteredStates.length} selected` : 'All states'}
            </div>
          </div>
        </foreignObject>

        {/* Data Order Filter - Positioned above chart */}
        <foreignObject x={margin.left} y={10} width="300" height="60">
          <div style={{ 
            background: 'rgba(0,0,0,0.8)', 
            padding: '8px', 
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.2)'
          }}>
            <label style={{ color: 'white', fontSize: '12px', marginBottom: '5px', display: 'block' }}>
              Order by Emotion:
            </label>
            <select 
              value={orderOption?.value || ''}
              onChange={(e) => onDataOrderSelection(e.target.value ? {value: e.target.value, label: e.target.value} : null)}
              style={{
                width: '100%',
                background: 'rgba(255,255,255,0.1)',
                color: 'white',
                border: '1px solid rgba(255,255,255,0.3)',
                borderRadius: '4px',
                padding: '4px',
                fontSize: '11px'
              }}
            >
              <option value="">Default (Alphabetical)</option>
              {orderOptions.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
        </foreignObject>

        {/* Range Slider - Bottom of chart */}
        <foreignObject x={margin.left} y={svgHeight - 100} width={width} height="80">
          <div style={{ 
            background: 'rgba(0,0,0,0.8)', 
            padding: '10px', 
            borderRadius: '8px',
            border: '1px solid rgba(255,255,255,0.2)'
          }}>
            <div style={{ color: 'white', fontSize: '12px', marginBottom: '8px', textAlign: 'center' }}>
              Emotion Score Range: {range[0].toFixed(2)} - {range[1].toFixed(2)}
            </div>
            <div style={{ position: 'relative', height: '20px' }}>
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.01" 
                value={tempRange[0]}
                onChange={(e) => handleSliderChange(0, parseFloat(e.target.value))}
                onMouseUp={(e) => handleSliderEnd(0, parseFloat(e.target.value))}
                style={{
                  position: 'absolute',
                  width: '100%',
                  height: '6px',
                  background: 'transparent',
                  outline: 'none',
                  opacity: 0.7,
                  cursor: 'pointer'
                }}
              />
              <input 
                type="range" 
                min="0" 
                max="1" 
                step="0.01" 
                value={tempRange[1]}
                onChange={(e) => handleSliderChange(1, parseFloat(e.target.value))}
                onMouseUp={(e) => handleSliderEnd(1, parseFloat(e.target.value))}
                style={{
                  position: 'absolute',
                  width: '100%',
                  height: '6px',
                  background: 'transparent',
                  outline: 'none',
                  opacity: 0.7,
                  cursor: 'pointer'
                }}
              />
            </div>
          </div>
        </foreignObject>

      </svg>
    </div>
  );
};

export default OriginalDotPlot;
