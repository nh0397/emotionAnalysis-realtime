import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import * as d3 from 'd3';
import TimeSeriesChart from './TimeSeriesChart';

const SimpleDotPlot = ({ data, dimensions, colorObjects }) => {
  // Debug logging for component props
  console.log("🔍 SimpleDotPlot Component Debug:");
  console.log("  - data length:", data?.length);
  console.log("  - data sample:", data?.slice(0, 2));
  console.log("  - dimensions:", dimensions);
  
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  
  // State management
  const [selectedLines, setSelectedLines] = useState([]);
  const [hoveredValue, setHoveredValue] = useState(null);
  const [selectedState, setSelectedState] = useState("");
  const [filteredStates, setFilteredStates] = useState([]);
  const [emotionRange, setEmotionRange] = useState([0, 1]);
  const [orderByEmotion, setOrderByEmotion] = useState("");
  const [selectedEmotions, setSelectedEmotions] = useState([]);
  const [showComparisonModal, setShowComparisonModal] = useState(false);
  const [timeSeriesData, setTimeSeriesData] = useState([]);
  const [loadingTimeSeries, setLoadingTimeSeries] = useState(false);

  // Chart dimensions - start from extreme left, minimal margins
  const isMobile = window.innerWidth < 768;
  const margin = { 
    top: 100, 
    right: isMobile ? 400 : 450, 
    bottom: 100, 
    left: 0 
  };
  const width = dimensions.width - margin.left - margin.right;
  const height = dimensions.height - margin.top - margin.bottom;
  const svgWidth = dimensions.width;
  const svgHeight = dimensions.height;

  // Extract unique states and emotions
  const allStates = [...new Set(data.map(d => d.state))].sort();
  const emotions = ['anger', 'fear', 'sadness', 'surprise', 'joy', 'anticipation', 'trust', 'disgust'];
  const sentimentCategories = ['positive', 'negative', 'neutral'];

  // Color scale
  const colorScale = d3.scaleOrdinal()
    .domain(emotions)
    .range(['#FF0000', '#FFA500', '#008000', '#0000FF', '#FFC0CB', '#FFD700', '#9400D3', '#00FFFF']);

  // Process and filter data
  const processedData = useMemo(() => {
    let filtered = data;
    
    // Apply state filter
    if (filteredStates.length > 0) {
      filtered = filtered.filter(d => filteredStates.includes(d.state));
    }
    
    // Apply emotion filter
    if (selectedEmotions.length > 0) {
      filtered = filtered.map(d => {
        const filteredEmotions = {};
        emotions.forEach(emotion => {
          if (selectedEmotions.includes(emotion)) {
            const value = d[emotion] || 0;
            if (value >= emotionRange[0] && value <= emotionRange[1]) {
              filteredEmotions[emotion] = value;
            } else {
              filteredEmotions[emotion] = 0;
            }
          } else {
            filteredEmotions[emotion] = 0;
          }
        });
        return { ...d, ...filteredEmotions };
      });
    } else {
      // Apply emotion range filter when no specific emotions selected
      filtered = filtered.map(d => {
        const filteredEmotions = {};
        emotions.forEach(emotion => {
          const value = d[emotion] || 0;
          if (value >= emotionRange[0] && value <= emotionRange[1]) {
            filteredEmotions[emotion] = value;
          } else {
            filteredEmotions[emotion] = 0;
          }
        });
        return { ...d, ...filteredEmotions };
      });
    }
    
    // Apply ordering
    if (orderByEmotion) {
      filtered.sort((a, b) => (b[orderByEmotion] || 0) - (a[orderByEmotion] || 0));
    }
    
    console.log("🔍 ProcessedData Debug:");
    console.log("  - Input data length:", data?.length);
    console.log("  - Filtered states:", filteredStates);
    console.log("  - Selected emotions:", selectedEmotions);
    console.log("  - Output filtered length:", filtered?.length);
    console.log("  - Sample filtered data:", filtered?.slice(0, 2));
    
    return filtered;
  }, [data, filteredStates, emotionRange, orderByEmotion, selectedEmotions]);

  // Scales
  const scales = useMemo(() => {
    if (!processedData || processedData.length === 0 || !width || !height) {
      return null;
    }

    const xScale = d3.scaleLinear()
      .domain([0, 1])
      .range([0, width]);

    const yScale = d3.scaleBand()
      .domain(processedData.map(d => d.state))
      .range([0, height])
      .padding(0.1);

    return { xScale, yScale, colorScale };
  }, [processedData, width, height]);

  // Event handlers
  const handleLineClick = useCallback((state) => {
    setSelectedLines(prev => {
      const newSelection = prev.includes(state) 
        ? prev.filter(s => s !== state)
        : [...prev, state].slice(-2);
      
      // Show comparison modal when exactly 2 lines are selected
      if (newSelection.length === 2) {
        console.log("🔍 Opening comparison modal for states:", newSelection);
        console.log("🔍 Available processedData:", processedData);
        console.log("🔍 Selected states data:", {
          state1: processedData.find(d => d.state === newSelection[0]),
          state2: processedData.find(d => d.state === newSelection[1])
        });
        setShowComparisonModal(true);
      } else {
        setShowComparisonModal(false);
      }
      
      return newSelection;
    });
  }, [processedData]);

  const handleTickClick = useCallback((state) => {
    setSelectedState(state);
    fetchTimeSeriesData(state);
  }, []);

  const fetchTimeSeriesData = useCallback(async (stateCode) => {
    if (!stateCode) return;
    
    setLoadingTimeSeries(true);
    try {
      console.log(`🕒 Fetching time series data for ${stateCode}...`);
      const response = await fetch(`http://localhost:9000/timeSeriesData/${stateCode}`);
      
      console.log(`🔍 Response status: ${response.status}`);
      console.log(`🔍 Response headers:`, response.headers);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ API Error: ${response.status} - ${errorText}`);
        throw new Error(`API Error: ${response.status} - ${errorText}`);
      }
      
      const data = await response.json();
      
      console.log(`📊 Time series data for ${stateCode}:`, {
        count: data.length,
        sample: data.slice(0, 3)
      });
      
      setTimeSeriesData(data);
    } catch (error) {
      console.error(`❌ Error fetching time series data for ${stateCode}:`, error);
      setTimeSeriesData([]); // Clear data on error
    } finally {
      setLoadingTimeSeries(false);
    }
  }, []);

  const handleStateFilter = useCallback((states) => {
    setFilteredStates(states);
  }, []);

  const handleEmotionToggle = useCallback((emotion) => {
    setSelectedEmotions(prev => 
      prev.includes(emotion)
        ? prev.filter(e => e !== emotion)
        : [...prev, emotion]
    );
  }, []);

  const resetFilters = useCallback(() => {
    setFilteredStates([]);
    setEmotionRange([0, 1]);
    setOrderByEmotion("");
    setSelectedLines([]);
    setHoveredValue(null);
    setSelectedEmotions([]);
    setShowComparisonModal(false);
  }, []);

  // Main rendering effect
  useEffect(() => {
    if (!svgRef.current || !processedData || processedData.length === 0 || !scales) return;
    
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
    if (!svgRef.current || !processedData || processedData.length === 0) {
      console.log("Cannot render chart: missing data or ref");
      return;
    }

    const container = d3.select(svgRef.current);
    if (container.empty()) {
      console.log("Cannot render chart: container is empty");
      return;
    }
    
    container.selectAll("*").remove();

    const svg = container.append("svg")
      .attr("width", "100%")
      .attr("height", "100%")
      .attr("viewBox", `0 0 ${svgWidth} ${svgHeight}`)
      .attr("preserveAspectRatio", "xMidYMid meet");

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Add axes
    if (scales && scales.xScale && scales.yScale) {
      g.append("g")
        .attr("class", "x-axis")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(scales.xScale))
        .selectAll("text")
        .style("font-size", "12px")
        .style("font-weight", "500")
        .style("fill", "#ffffff");

      // Make X-axis lines visible
      g.select(".x-axis")
        .selectAll("line")
        .style("stroke", "rgba(255, 255, 255, 0.3)");

      g.select(".x-axis")
        .select(".domain")
        .style("stroke", "rgba(255, 255, 255, 0.3)");

      g.append("g")
        .attr("class", "y-axis")
        .call(d3.axisLeft(scales.yScale))
        .selectAll("text")
        .style("text-anchor", "end")
        .style("font-size", "12px")
        .style("font-weight", "500")
        .style("fill", "#ffffff")
        .style("cursor", "pointer")
        .on("click", function(event, d) {
          handleTickClick(d);
        });

      // Make Y-axis lines visible
      g.select(".y-axis")
        .selectAll("line")
        .style("stroke", "rgba(255, 255, 255, 0.3)");

      g.select(".y-axis")
        .select(".domain")
        .style("stroke", "rgba(255, 255, 255, 0.3)");
    }



    // Add state lines connecting emotion dots
    processedData.forEach((stateData) => {
      const stateY = scales.yScale(stateData.state);
      
      // Always compute min/max from ALL eight emotions (original data),
      // independent of current emotion filters
      const originalRow = (data || []).find(d => d.state === stateData.state) || stateData;
      const allEmotionValues = emotions
        .map(e => parseFloat(originalRow[e] ?? 0) || 0)
        .filter(v => !Number.isNaN(v));
      if (allEmotionValues.length > 0) {
        const minVal = d3.min(allEmotionValues);
        const maxVal = d3.max(allEmotionValues);
        if (minVal != null && maxVal != null) {
          g.append("line")
            .attr("class", "state-range-line")
            .attr("x1", scales.xScale(minVal))
            .attr("x2", scales.xScale(maxVal))
            .attr("y1", stateY + scales.yScale.bandwidth() / 2)
            .attr("y2", stateY + scales.yScale.bandwidth() / 2)
            .attr("stroke", "rgba(255, 255, 255, 0.35)")
            .attr("stroke-width", 3)
            .attr("stroke-linecap", "round")
            .lower();
        }
      }

      // Get all emotion values for this state
      const emotionValues = emotions
        .map(emotion => ({
          emotion,
          value: stateData[emotion] || 0,
          x: scales.xScale(stateData[emotion] || 0)
        }))
        .filter(d => d.value > 0);
      
      // Only proceed if we have valid emotion values
      if (emotionValues && emotionValues.length > 0) {
        // Draw connecting line between emotion dots for each state
        if (emotionValues.length > 1) {
          const line = d3.line()
            .x(d => d.x)
            .y(() => stateY + scales.yScale.bandwidth() / 2);
          
          g.append("path")
            .attr("class", "state-line")
            .attr("d", line(emotionValues))
            .attr("stroke", selectedLines.includes(stateData.state) ? "#ffffff" : "rgba(255, 255, 255, 0.6)")
            .attr("stroke-width", selectedLines.includes(stateData.state) ? 3 : 2)
            .attr("fill", "none")
            .style("cursor", "pointer")
            .on("click", () => handleLineClick(stateData.state));
        }
        
        // Add emotion dots
        emotionValues.forEach(({ emotion, value, x }) => {
          if (value > 0 && !isNaN(x)) {
            g.append("circle")
              .attr("cx", x)
              .attr("cy", stateY + scales.yScale.bandwidth() / 2)
              .attr("r", 6)
              .attr("fill", colorScale(emotion))
              .attr("stroke", selectedLines.includes(stateData.state) ? "#ffffff" : "rgba(255, 255, 255, 0.8)")
              .attr("stroke-width", selectedLines.includes(stateData.state) ? 3 : 1)
              .style("cursor", "pointer")
              .on("mouseover", function(event) {
                d3.select(this).attr("r", 8);
                
                // Show tooltip
                const tooltip = d3.select("body").append("div")
                  .attr("class", "emotion-tooltip")
                  .style("position", "absolute")
                  .style("background", "rgba(0, 0, 0, 0.9)")
                  .style("color", "white")
                  .style("padding", "8px 12px")
                  .style("border-radius", "6px")
                  .style("font-size", "12px")
                  .style("pointer-events", "none")
                  .style("z-index", "1000");
                
                tooltip.html(`
                  <strong>${stateData.state}</strong><br/>
                  ${emotion}: ${value.toFixed(3)}<br/>
                  <small>Click to select state</small>
                `);
                
                tooltip.style("left", (event.pageX + 10) + "px")
                       .style("top", (event.pageY - 10) + "px");
              })
              .on("mouseout", function() {
                d3.select(this).attr("r", 6);
                d3.selectAll(".emotion-tooltip").remove();
              })
              .on("click", () => handleLineClick(stateData.state));
          }
        });
      }
    });

    // Add axis labels
    g.append("text")
      .attr("x", width / 2)
      .attr("y", height + 60)
      .style("text-anchor", "middle")
      .style("font-size", "14px")
      .style("font-weight", "bold")
      .style("fill", "#ffffff")
      .text("Emotion Scores");

    g.append("text")
      .attr("transform", "rotate(-90)")
      .attr("y", -30)
      .attr("x", -height / 2)
      .style("text-anchor", "middle")
      .style("font-size", "14px")
      .style("font-weight", "bold")
      .style("fill", "#ffffff")
      .text("States");

    // Add grid lines for better readability
    g.append("g")
      .attr("class", "grid")
      .attr("transform", `translate(0,${height})`)
      .call(d3.axisBottom(scales.xScale)
        .tickSize(-height)
        .tickFormat("")
      )
      .selectAll("line")
      .style("stroke", "rgba(255, 255, 255, 0.1)")
      .style("stroke-dasharray", "2,2");

    g.append("g")
      .attr("class", "grid")
      .call(d3.axisLeft(scales.yScale)
        .tickSize(-width)
        .tickFormat("")
      )
      .selectAll("line")
      .style("stroke", "rgba(255, 255, 255, 0.1)")
      .style("stroke-dasharray", "2,2");

    // Right-side stacked bar chart for tweet distribution (neutral/positive/negative)
    const sideChartWidth = 200;
    const rightBarsX = width + 30;

    const dataWithSums = processedData.map(d => ({
      ...d,
      senti_neutral_count: parseInt(d.sentiment_neutral_count || 0, 10),
      senti_positive_count: parseInt(d.sentiment_positive_count || 0, 10),
      senti_negative_count: parseInt(d.sentiment_negative_count || 0, 10),
    })).map(d => ({
      ...d,
      sum: (d.senti_neutral_count || 0) + (d.senti_positive_count || 0) + (d.senti_negative_count || 0)
    }));

    const maxSum = d3.max(dataWithSums, d => d.sum) || 1;
    const widthScale = d3.scaleSqrt().domain([0, maxSum]).range([30, sideChartWidth - 20]);
    const colors = { neutral: '#5C85FF', positive: '#85e085', negative: '#FF8080' };

    // Tooltip for side bars
    const barTooltip = d3.select('body')
      .selectAll('.tweet-dist-tooltip')
      .data([null])
      .join('div')
      .attr('class', 'tweet-dist-tooltip')
      .style('position', 'absolute')
      .style('padding', '10px 12px')
      .style('background', 'rgba(0,0,0,0.9)')
      .style('color', '#fff')
      .style('border', '1px solid rgba(255,255,255,0.2)')
      .style('border-radius', '6px')
      .style('font-size', '12px')
      .style('pointer-events', 'none')
      .style('z-index', 1000)
      .style('opacity', 0);

    const drawSideBars = (container, alignRight = true) => {
      const sentiments = ['neutral', 'positive', 'negative'];
      sentiments.forEach((sentiment, index) => {
        container.selectAll(`.bar-${sentiment}`)
          .data(dataWithSums)
          .join('rect')
          .attr('class', `bar-${sentiment}`)
          .attr('y', d => scales.yScale(d.state) + (scales.yScale.bandwidth() - 6) / 2)
          .attr('height', 6)
          .attr('fill', colors[sentiment])
          .attr('opacity', 0.8)
          .on('mouseover', (event, d) => {
            barTooltip.style('opacity', 1);
          })
          .on('mousemove', (event, d) => {
            const html = `<strong>${d.state}</strong><br/>`
              + `Positive: ${d.senti_positive_count?.toLocaleString?.() || d.senti_positive_count || 0}<br/>`
              + `Negative: ${d.senti_negative_count?.toLocaleString?.() || d.senti_negative_count || 0}<br/>`
              + `Neutral: ${d.senti_neutral_count?.toLocaleString?.() || d.senti_neutral_count || 0}`;
            barTooltip
              .html(html)
              .style('left', (event.pageX + 12) + 'px')
              .style('top', (event.pageY - 10) + 'px');
          })
          .on('mouseout', () => {
            barTooltip.style('opacity', 0);
          })
          .attr('x', d => {
            const counts = {
              neutral: d.senti_neutral_count || 0,
              positive: d.senti_positive_count || 0,
              negative: d.senti_negative_count || 0,
            };
            const prevSentiments = sentiments.slice(0, index);
            const prevWidth = d3.sum(prevSentiments.map(s => widthScale(counts[s])));
            const thisWidth = widthScale(counts[sentiment]);
            if (alignRight) {
              return sideChartWidth - thisWidth - prevWidth;
            }
            return prevWidth;
          })
          .attr('width', d => {
            const counts = {
              neutral: d.senti_neutral_count || 0,
              positive: d.senti_positive_count || 0,
              negative: d.senti_negative_count || 0,
            };
            return widthScale(counts[sentiment]);
          });
      });
    };

    // Right stacked bars (left-aligned)
    const rightBars = g.append('g')
      .attr('transform', `translate(${rightBarsX}, 0)`);
    drawSideBars(rightBars, false);

    // Legend for tweet distribution (inside right bar area, top-right)
    const legendItems = [
      { key: 'neutral', label: 'Neutral', color: colors.neutral },
      { key: 'positive', label: 'Positive', color: colors.positive },
      { key: 'negative', label: 'Negative', color: colors.negative },
    ];
    const legend = rightBars.append('g')
      .attr('transform', `translate(${Math.max(0, sideChartWidth - 200)}, ${-14})`);
    const li = legend.selectAll('g')
      .data(legendItems)
      .join('g')
      .attr('transform', (d, i) => `translate(${i * 65}, 0)`);
    li.append('rect')
      .attr('width', 10)
      .attr('height', 10)
      .attr('fill', d => d.color)
      .attr('opacity', 0.9);
    li.append('text')
      .attr('x', 14)
      .attr('y', 9)
      .style('fill', '#ffffff')
      .style('font-size', '11px')
      .text(d => d.label);

    // Add tornado chart if two states are selected
    if (selectedLines.length === 2) {
      const state1Data = processedData.find(d => d.state === selectedLines[0]);
      const state2Data = processedData.find(d => d.state === selectedLines[1]);
      
      if (state1Data && state2Data) {
        const tornadoData = emotions.map(emotion => ({
          emotion,
          state1: state1Data[emotion] || 0,
          state2: state2Data[emotion] || 0
        }));
        
        // Position tornado chart in top-right
        const tornadoContainer = g.append("g")
          .attr("transform", `translate(${width - 200}, 20)`);
        
        // Simple tornado chart visualization
        tornadoData.forEach((d, i) => {
          const y = i * 20;
          const maxValue = Math.max(d.state1, d.state2);
          
          if (maxValue > 0) {
            // State 1 bar (left)
            tornadoContainer.append("rect")
              .attr("x", -scales.xScale(d.state1))
              .attr("y", y)
              .attr("width", scales.xScale(d.state1))
              .attr("height", 15)
              .attr("fill", colorScale(d.emotion))
              .attr("opacity", 0.8);
            
            // State 2 bar (right)
            tornadoContainer.append("rect")
              .attr("x", 0)
              .attr("y", y)
              .attr("width", scales.xScale(d.state2))
              .attr("height", 15)
              .attr("opacity", 0.8);
            
            // Emotion label
            tornadoContainer.append("text")
              .attr("x", -scales.xScale(d.state1) - 10)
              .attr("y", y + 10)
              .attr("text-anchor", "end")
              .style("font-size", "10px")
              .style("fill", "#ffffff")
              .text(d.emotion);
          }
        });
        
        // Add state labels
        tornadoContainer.append("text")
          .attr("x", -100)
          .attr("y", -10)
          .attr("text-anchor", "middle")
          .style("font-size", "12px")
          .style("font-weight", "bold")
          .style("fill", "#ffffff")
          .text(state1Data.state);
        
        tornadoContainer.append("text")
          .attr("x", 100)
          .attr("y", -10)
          .attr("text-anchor", "middle")
          .style("font-size", "12px")
          .style("font-weight", "bold")
          .style("fill", "#ffffff")
          .text(state2Data.state);
      }
    }
  }, [processedData, hoveredValue, selectedLines, scales, width, height, margin, emotions, colorScale, handleTickClick, handleLineClick]);

  // Use state to track window size for responsive layout
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  
  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div ref={containerRef} style={{ 
      width: '100%', 
      height: 'calc(100vh - 40px)',
      position: 'relative',
      background: 'linear-gradient(135deg, rgba(0,0,0,0.95) 0%, rgba(26,26,26,0.9) 50%, rgba(51,51,51,0.85) 100%)',
      padding: '20px',
      display: 'flex',
      flexDirection: windowWidth < 1024 ? 'column' : 'row',
      gap: '20px'
    }}>
      
      {/* Emotion Legend - Top, Selectable */}
      <div style={{
        position: 'absolute',
        top: '20px',
        left: '20px',
        right: '20px',
        background: 'rgba(0, 0, 0, 0.6)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        borderRadius: '12px',
        padding: '15px',
        zIndex: 1000
      }}>
        <h4 style={{ 
          color: '#ffffff', 
          margin: '0 0 15px 0',
          fontSize: '16px',
          textAlign: 'center'
        }}>
          Select Emotions to Display
        </h4>
        <div style={{ 
          display: 'flex', 
          flexWrap: 'wrap', 
          gap: '12px', 
          justifyContent: 'center' 
        }}>
          {emotions.map(emotion => (
            <button
              key={emotion}
              onClick={() => handleEmotionToggle(emotion)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                borderRadius: '20px',
                border: selectedEmotions.includes(emotion) 
                  ? '2px solid #ffffff' 
                  : '1px solid rgba(255, 255, 255, 0.3)',
                background: selectedEmotions.includes(emotion)
                  ? 'rgba(255, 255, 255, 0.2)'
                  : 'rgba(0, 0, 0, 0.4)',
                color: '#ffffff',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: selectedEmotions.includes(emotion) ? 'bold' : 'normal',
                transition: 'all 0.2s ease'
              }}
            >
              <div style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                background: colorScale(emotion)
              }} />
              {emotion.charAt(0).toUpperCase() + emotion.slice(1)}
            </button>
          ))}
        </div>
      </div>
      
      {/* Chart Container - Takes full canvas, starts from extreme left */}
      <div 
        ref={svgRef} 
        style={{ 
          width: windowWidth < 1024 ? '100%' : 'calc(100% - 320px)',
          height: '100%', 
          position: 'relative',
          marginTop: '100px',
          flex: windowWidth < 1024 ? '1' : '1 1 auto'
        }}
      >
        {/* Main Chart SVG - will be populated by D3 */}
      </div>
      
      {/* Filter Controls - Responsive: columnar on small screens, sidebar on large */}
      {!selectedState && (
        <div style={{
          position: windowWidth >= 1024 ? 'absolute' : 'relative',
          top: windowWidth >= 1024 ? '210px' : 'auto',
          right: windowWidth >= 1024 ? '40px' : 'auto',
          marginTop: windowWidth >= 1024 ? '0' : '20px',
          marginBottom: windowWidth >= 1024 ? '0' : '20px',
          background: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: '12px',
          padding: '20px',
          width: windowWidth < 768 ? '100%' : (windowWidth < 1024 ? '100%' : '280px'),
          height: 'auto',
          overflow: 'visible',
          maxWidth: windowWidth >= 1024 ? '280px' : '100%',
          zIndex: windowWidth >= 1024 ? 1000 : 'auto',
          flexShrink: 0
        }}>
          
          {/* State Filter */}
          <div style={{ marginBottom: '20px' }}>
            <label style={{ 
              color: '#ffffff', 
              fontWeight: 'bold', 
              marginBottom: '8px', 
              display: 'block',
              fontSize: '14px'
            }}>
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
                height: '80px', 
                padding: '8px',
                borderRadius: '6px',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                background: 'rgba(0, 0, 0, 0.6)',
                color: '#ffffff',
                width: '100%'
              }}
            >
              {allStates.map(state => (
                <option key={state} value={state} style={{ background: '#000', color: '#fff' }}>
                  {state}
                </option>
              ))}
            </select>
          </div>

          {/* Emotion Range Filter */}
          <div style={{ marginBottom: '15px' }}>
            <label style={{ 
              color: '#ffffff', 
              fontWeight: 'bold', 
              marginBottom: '6px', 
              display: 'block',
              fontSize: '13px'
            }}>
              Emotion Range:
            </label>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '4px' }}>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={emotionRange[0]}
                onChange={(e) => setEmotionRange([parseFloat(e.target.value), emotionRange[1]])}
                style={{ flex: 1 }}
              />
              <span style={{ color: '#ffffff', fontSize: '11px', minWidth: '25px' }}>
                {emotionRange[0].toFixed(2)}
              </span>
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <input
                type="range"
                min="0"
                max="1"
                step="0.01"
                value={emotionRange[1]}
                onChange={(e) => setEmotionRange([emotionRange[0], parseFloat(e.target.value)])}
                style={{ flex: 1 }}
              />
              <span style={{ color: '#ffffff', fontSize: '11px', minWidth: '25px' }}>
                {emotionRange[1].toFixed(2)}
              </span>
            </div>
          </div>

          {/* Order By Emotion */}
          <div style={{ marginBottom: '15px' }}>
            <label style={{ 
              color: '#ffffff', 
              fontWeight: 'bold', 
              marginBottom: '6px', 
              display: 'block',
              fontSize: '13px'
            }}>
              Order By:
            </label>
            <select
              value={orderByEmotion}
              onChange={(e) => setOrderByEmotion(e.target.value)}
              style={{
                width: '100%',
                padding: '8px',
                borderRadius: '6px',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                background: 'rgba(0, 0, 0, 0.6)',
                color: '#ffffff'
              }}
            >
              <option value="">No Order</option>
              {emotions.map(emotion => (
                <option key={emotion} value={emotion} style={{ background: '#000', color: '#fff' }}>
                  {emotion.charAt(0).toUpperCase() + emotion.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Reset Filters */}
          <button
            onClick={resetFilters}
            style={{
              width: '100%',
              padding: '10px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: 'bold',
              marginBottom: '20px'
            }}
          >
            Reset All Filters
          </button>
        </div>
      )}

      {/* Time Series Chart - Full Screen Overlay */}
      {selectedState && timeSeriesData && (
        <div style={{ 
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(0, 0, 0, 0.95)',
          backdropFilter: 'blur(10px)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{ 
            background: 'rgba(0, 0, 0, 0.8)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '16px',
            padding: '30px',
            maxWidth: '90%',
            maxHeight: '90%',
            overflow: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, color: '#ffffff', fontSize: '24px' }}>
                Time Series Analysis for {selectedState}
              </h3>
              <button 
                onClick={() => setSelectedState("")}
                style={{
                  padding: '12px 20px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  fontSize: '14px'
                }}
              >
                ← Back to Dot Plot
              </button>
            </div>
            {loadingTimeSeries ? (
              <div style={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                justifyContent: 'center',
                height: '400px',
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '8px'
              }}>
                <div className="spinner"></div>
                <p style={{ color: '#ffffff', marginTop: '20px' }}>
                  Loading time series data for {selectedState}...
                </p>
              </div>
            ) : timeSeriesData.length > 0 ? (
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
            ) : (
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                height: '400px',
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '8px',
                color: '#ffffff'
              }}>
                <p>Click on a state name to view time series data</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Comparison Modal - Shows when 2 lines are selected */}
      {showComparisonModal && selectedLines.length === 2 && (
        <div style={{ 
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'rgba(0, 0, 0, 0.95)',
          backdropFilter: 'blur(10px)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{ 
            background: 'rgba(0, 0, 0, 0.8)',
            border: '1px solid rgba(255, 255, 255, 0.2)',
            borderRadius: '16px',
            padding: '30px',
            maxWidth: '95%',
            maxHeight: '95%',
            overflow: 'auto'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h3 style={{ margin: 0, color: '#ffffff', fontSize: '24px' }}>
                Emotion Comparison: {selectedLines[0]} vs {selectedLines[1]}
              </h3>
              <button 
                onClick={() => {
                  setShowComparisonModal(false);
                  setSelectedLines([]);
                }}
                style={{
                  padding: '12px 20px',
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: 'pointer',
                  fontWeight: 'bold',
                  fontSize: '14px'
                }}
              >
                ← Back to Dot Plot
              </button>
            </div>
            
            {/* Charts Container */}
            <div style={{ 
              display: 'flex', 
              flexDirection: window.innerWidth < 1200 ? 'column' : 'row',
              gap: '30px',
              alignItems: 'flex-start'
            }}>
              {/* Radar Chart */}
              <div style={{ 
                flex: 1,
                minWidth: '400px',
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '12px',
                padding: '20px',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}>
                <h4 style={{ 
                  margin: '0 0 15px 0', 
                  color: '#ffffff', 
                  fontSize: '18px',
                  textAlign: 'center'
                }}>
                  Emotion Radar Chart
                </h4>
                
                {/* Debug Info */}
                <div style={{ 
                  background: 'rgba(255, 255, 255, 0.1)', 
                  padding: '10px', 
                  borderRadius: '8px', 
                  marginBottom: '15px',
                  fontSize: '12px',
                  color: '#ffffff'
                }}>
                  <div>Selected States: {selectedLines.join(' vs ')}</div>
                  <div>Data Available: {processedData.length} records</div>
                  <div>State 1 Data: {processedData.find(d => d.state === selectedLines[0]) ? '✅' : '❌'}</div>
                  <div>State 2 Data: {processedData.find(d => d.state === selectedLines[1]) ? '✅' : '❌'}</div>
                </div>
                <svg width="600" height="500" style={{ background: 'transparent' }}>
                  {(() => {
                    const state1Data = processedData.find(d => d.state === selectedLines[0]);
                    const state2Data = processedData.find(d => d.state === selectedLines[1]);
                    
                    // Debug logging
                    console.log("🔍 Radar Chart Debug:");
                    console.log("  - selectedLines:", selectedLines);
                    console.log("  - state1Data:", state1Data);
                    console.log("  - state2Data:", state2Data);
                    console.log("  - processedData length:", processedData.length);
                    
                    if (!state1Data || !state2Data) {
                      console.log("❌ Missing state data for radar chart");
                      return (
                        <text x="300" y="250" textAnchor="middle" fill="#ffffff" fontSize="16px">
                          ❌ Missing data for comparison
                        </text>
                      );
                    }
                    
                    const centerX = 300;
                    const centerY = 250;
                    const radius = 150;
                    const numEmotions = emotions.length;
                    
                    // Calculate points for radar chart
                    const getPoint = (emotion, value, stateIndex) => {
                      const angle = (emotions.indexOf(emotion) / numEmotions) * 2 * Math.PI - Math.PI / 2;
                      const distance = radius * value;
                      const x = centerX + distance * Math.cos(angle);
                      const y = centerY + distance * Math.sin(angle);
                      return { x, y, angle };
                    };
                    
                    // Draw radar grid
                    const gridLevels = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0];
                    gridLevels.forEach(level => {
                      const points = emotions.map((emotion, i) => {
                        const angle = (i / numEmotions) * 2 * Math.PI - Math.PI / 2;
                        const x = centerX + radius * level * Math.cos(angle);
                        const y = centerY + radius * level * Math.sin(angle);
                        return { x, y };
                      });
                      
                      // Close the polygon
                      points.push(points[0]);
                      
                      // Draw grid lines
                      return (
                        <polygon
                          key={`grid-${level}`}
                          points={points.map(p => `${p.x},${p.y}`).join(' ')}
                          fill="none"
                          stroke="rgba(255, 255, 255, 0.1)"
                          strokeWidth="1"
                        />
                      );
                    });
                    
                    // Draw emotion axis lines
                    const axisLines = emotions.map((emotion, i) => {
                      const angle = (i / numEmotions) * 2 * Math.PI - Math.PI / 2;
                      const x = centerX + radius * Math.cos(angle);
                      const y = centerY + radius * Math.sin(angle);
                      
                      return (
                        <line
                          key={`axis-${emotion}`}
                          x1={centerX}
                          y1={centerY}
                          x2={x}
                          y2={y}
                          stroke="rgba(255, 255, 255, 0.2)"
                          strokeWidth="1"
                        />
                      );
                    });
                    
                    // Draw emotion labels
                    const emotionLabels = emotions.map((emotion, i) => {
                      const angle = (i / numEmotions) * 2 * Math.PI - Math.PI / 2;
                      const labelRadius = radius + 25;
                      const x = centerX + labelRadius * Math.cos(angle);
                      const y = centerY + labelRadius * Math.sin(angle);
                      
                      return (
                        <text
                          key={`label-${emotion}`}
                          x={x}
                          y={y}
                          textAnchor="middle"
                          dominantBaseline="middle"
                          fill="#ffffff"
                          fontSize="12px"
                        >
                          {emotion}
                        </text>
                      );
                    });
                    
                    // Draw State 1 polygon
                    const state1Points = emotions.map(emotion => {
                      const value = state1Data[emotion] || 0;
                      return getPoint(emotion, value, 0);
                    });
                    state1Points.push(state1Points[0]); // Close polygon
                    
                    const state1Polygon = (
                      <polygon
                        points={state1Points.map(p => `${p.x},${p.y}`).join(' ')}
                        fill="rgba(255, 119, 0, 0.3)"
                        stroke="#ff7700"
                        strokeWidth="3"
                      />
                    );
                    
                    // Draw State 2 polygon
                    const state2Points = emotions.map(emotion => {
                      const value = state2Data[emotion] || 0;
                      return getPoint(emotion, value, 1);
                    });
                    state2Points.push(state2Points[0]); // Close polygon
                    
                    const state2Polygon = (
                      <polygon
                        points={state2Points.map(p => `${p.x},${p.y}`).join(' ')}
                        fill="rgba(26, 118, 255, 0.3)"
                        stroke="#1a76ff"
                        strokeWidth="2"
                      />
                    );
                    
                    // Draw data points
                    const state1DataPoints = emotions.map(emotion => {
                      const value = state1Data[emotion] || 0;
                      const point = getPoint(emotion, value, 0);
                      return (
                        <circle
                          key={`point1-${emotion}`}
                          cx={point.x}
                          cy={point.y}
                          r="3"
                          fill="#ff7700"
                        />
                      );
                    });
                    
                    const state2DataPoints = emotions.map(emotion => {
                      const value = state2Data[emotion] || 0;
                      const point = getPoint(emotion, value, 1);
                      return (
                        <circle
                          key={`point2-${emotion}`}
                          cx={point.x}
                          cy={point.y}
                          r="3"
                          fill="#1a76ff"
                        />
                      );
                    });
                    
                    // Legend
                    const legend = (
                      <g>
                        <circle cx={centerX - 60} cy={centerY + radius + 20} r="6" fill="#ff7700" />
                        <text x={centerX - 50} y={centerY + radius + 20} fill="#ffffff" fontSize="12px" dominantBaseline="middle">
                          {selectedLines[0]}
                        </text>
                        <circle cx={centerX + 20} cy={centerY + radius + 20} r="6" fill="#1a76ff" />
                        <text x={centerX + 30} y={centerY + radius + 20} fill="#ffffff" fontSize="12px" dominantBaseline="middle">
                          {selectedLines[1]}
                        </text>
                      </g>
                    );
                    
                    return (
                      <g>
                        {gridLevels.map(level => {
                          const points = emotions.map((emotion, i) => {
                            const angle = (i / numEmotions) * 2 * Math.PI - Math.PI / 2;
                            const x = centerX + radius * level * Math.cos(angle);
                            const y = centerY + radius * level * Math.sin(angle);
                            return { x, y };
                          });
                          points.push(points[0]);
                          
                          return (
                            <polygon
                              key={`grid-${level}`}
                              points={points.map(p => `${p.x},${p.y}`).join(' ')}
                              fill="none"
                              stroke="rgba(255, 255, 255, 0.1)"
                              strokeWidth="1"
                            />
                          );
                        })}
                        {axisLines}
                        {emotionLabels}
                        {state1Polygon}
                        {state2Polygon}
                        {state1DataPoints}
                        {state2DataPoints}
                        {legend}
                      </g>
                    );
                  })()}
                </svg>
              </div>

                            {/* Difference Bar Chart */}
              <div style={{ 
                flex: 1,
                minWidth: '400px',
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '12px',
                padding: '20px',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}>
                <h4 style={{ 
                  margin: '0 0 15px 0', 
                  color: '#ffffff', 
                  fontSize: '18px',
                  textAlign: 'center'
                }}>
                  Emotion Differences
                </h4>
                
                {/* Debug Info */}
                <div style={{ 
                  background: 'rgba(255, 255, 255, 0.1)', 
                  padding: '10px', 
                  borderRadius: '8px', 
                  marginBottom: '15px',
                  fontSize: '12px',
                  color: '#ffffff'
                }}>
                  <div>State 1: {selectedLines[0]} - {processedData.find(d => d.state === selectedLines[0]) ? '✅' : '❌'}</div>
                  <div>State 2: {selectedLines[1]} - {processedData.find(d => d.state === selectedLines[1]) ? '✅' : '❌'}</div>
                </div>
                <svg width="400" height="300" style={{ background: 'transparent' }}>
                  {(() => {
                    const state1Data = processedData.find(d => d.state === selectedLines[0]);
                    const state2Data = processedData.find(d => d.state === selectedLines[1]);
                    
                    console.log("🔍 Difference Bar Chart Debug:");
                    console.log("  - state1Data:", state1Data);
                    console.log("  - state2Data:", state2Data);
                    
                    if (!state1Data || !state2Data) {
                      console.log("❌ Missing state data for difference chart");
                      return (
                        <text x="200" y="150" textAnchor="middle" fill="#ffffff" fontSize="16px">
                          ❌ Missing data for comparison
                        </text>
                      );
                    }
                    
                    const chartWidth = 300;
                    const chartHeight = 200;
                    const margin = { top: 20, right: 20, bottom: 40, left: 80 };
                    const innerWidth = chartWidth - margin.left - margin.right;
                    const innerHeight = chartHeight - margin.top - margin.bottom;
                    
                    const yScale = d3.scaleBand()
                      .domain(emotions)
                      .range([margin.top, margin.top + innerHeight])
                      .padding(0.1);
                    
                    const xScale = d3.scaleLinear()
                      .domain([-1, 1])
                      .range([0, innerWidth]);
                    
                    const differences = emotions.map(emotion => ({
                      emotion,
                      difference: (state1Data[emotion] || 0) - (state2Data[emotion] || 0)
                    }));
                    
                    return (
                      <g>
                        {/* Bars */}
                        {differences.map((item, i) => {
                          const y = yScale(item.emotion);
                          const barHeight = yScale.bandwidth();
                          const barWidth = Math.abs(xScale(item.difference) - xScale(0));
                          const x = item.difference > 0 ? xScale(0) : xScale(item.difference);
                          
                          return (
                            <rect
                              key={item.emotion}
                              x={margin.left + x}
                              y={y}
                              width={barWidth}
                              height={barHeight}
                              fill={item.difference > 0 ? "#4CAF50" : "#FF5722"}
                              opacity={0.8}
                            />
                          );
                        })}
                        
                        {/* Y-axis labels */}
                        {emotions.map((emotion, i) => {
                          const y = yScale(emotion) + yScale.bandwidth() / 2;
                          return (
                            <text
                              key={`label-${emotion}`}
                              x={margin.left - 10}
                              y={y}
                              textAnchor="end"
                              fill="#ffffff"
                              fontSize="10px"
                              dominantBaseline="middle"
                            >
                              {emotion}
                            </text>
                          );
                        })}
                        
                        {/* X-axis */}
                        <line
                          x1={margin.left + xScale(0)}
                          y1={margin.top}
                          x2={margin.left + xScale(0)}
                          y2={margin.top + innerHeight}
                          stroke="#ffffff"
                          strokeWidth="1"
                          opacity={0.5}
                        />
                        
                        {/* X-axis labels */}
                        <text
                          x={margin.left + xScale(-0.5)}
                          y={chartHeight - 10}
                          textAnchor="middle"
                          fill="#ffffff"
                          fontSize="10px"
                        >
                          {selectedLines[1]} Higher
                        </text>
                        <text
                          x={margin.left + xScale(0.5)}
                          y={chartHeight - 10}
                          textAnchor="middle"
                          fill="#ffffff"
                          fontSize="10px"
                        >
                          {selectedLines[0]} Higher
                        </text>
                      </g>
                    );
                  })()}
                </svg>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimpleDotPlot;
