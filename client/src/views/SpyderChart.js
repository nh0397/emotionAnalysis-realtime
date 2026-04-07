import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';

const SpiderChart = ({ data, width = 500, height = 500 }) => {
    if (!data || data.length === 0) return;
    const svgRef = useRef(null);
    const [highlightedIndex, setHighlightedIndex] = useState(null);

    var processedData = data.map(d => ({
        axes: [
            // Positive emotions
            { axis: 'joy', value: parseFloat(isNaN(d.joy) ? 0 : d.joy) },
            { axis: 'trust', value: parseFloat(isNaN(d.trust) ? 0 : d.trust) },
            { axis: 'surprise', value: parseFloat(isNaN(d.surprise) ? 0 : d.surprise) },
            { axis: 'positive', value: parseFloat(isNaN(d.positive) ? 0 : d.positive) },
            { axis: 'anticipation', value: parseFloat(isNaN(d.anticipation) ? 0 : d.anticipation) },

            // Negative emotions
            { axis: 'anger', value: parseFloat(isNaN(d.anger) ? 0 : d.anger) },
            { axis: 'fear', value: parseFloat(isNaN(d.fear) ? 0 : d.fear) },
            { axis: 'sadness', value: parseFloat(isNaN(d.sadness) ? 0 : d.sadness) },
            { axis: 'disgust', value: parseFloat(isNaN(d.disgust) ? 0 : d.disgust) },
            { axis: 'negative', value: parseFloat(isNaN(d.negative) ? 0 : d.negative) },
        ],
        color: d.color,
    }));

    console.log('processedData:', processedData);
    const generateLegend = (legendData) => {
        return legendData.map((item, index) => ({
            color: item.color,
            opacity: highlightedIndex === null || highlightedIndex === index ? 0.5 : 0.2,
            text: `State: ${item.state}`,
        }));
    };

    useEffect(() => {
        const svg = d3.select(svgRef.current);
        svg.selectAll('*').remove();

        // Configure chart properties
        const radius = Math.min(width - 100, height) / 2;
        const angleSlice = (2 * Math.PI) / processedData[0].axes.length;

        // Create scales
        const rScale = d3.scaleLinear()
            .domain([0, 1])
            .range([0, radius]);

        // Function to draw the chart
        const draw = () => {
            // Append a group for the chart
            const chartGroup = svg.append('g')
                .attr('transform', `translate(${(width) / 2}, ${(height) / 2})`);

            // Generate legend data
            const legendData = generateLegend(data);

            // Create legend group
            const legendGroup = svg.append('g')
                .attr('class', 'legend')
                .attr('transform', `translate(${width - 80}, ${height / 2 - legendData.length * 20 / 2})`);

            // Create legend items
            legendGroup.selectAll('.legend-item')
                .data(legendData)
                .enter().append('g')
                .attr('class', 'legend-item')
                .attr('transform', (d, i) => `translate(0, ${i * 20})`)
                .each(function (d, i) {
                    d3.select(this).append('rect')
                        .attr('width', 18)
                        .attr('height', 18)
                        .style('fill-opacity', d.opacity)
                        .style('fill', d.color)
                        .on('mouseenter', () => setHighlightedIndex(i))
                        .on('mouseleave', () => setHighlightedIndex(null));


                    d3.select(this).append('text')
                        .attr('x', 24)
                        .attr('y', 9)
                        .attr('dy', '.35em')
                        .style('text-anchor', 'start')
                        .style('font-size', '12px')
                        .text(d.text);
                });

            // Draw radial grid lines
            const radialGrid = chartGroup.selectAll('.radial-grid')
                .data(d3.range(0, 0.7, 0.1)) // updated data range
                .enter().append('g')
                .attr('class', 'radial-grid');

            radialGrid.append('circle')
                .attr('r', (d) => rScale(d))
                .style('stroke', '#cccccc')
                .style('stroke-width', '1px')
                .style('fill', 'none');

            radialGrid.append('text')
                .attr('x', 0)
                .attr('y', (d) => -rScale(d) * 1.1)
                .attr('dy', '0.35em')
                .style('text-anchor', 'middle')
                .style('font-size', '12px')
                .text((d) => (Math.round(d * 10) % 2 === 0) ? d.toFixed(1) : '');

            // Draw the radar chart polygons
            const radarLine = d3.lineRadial()
                .radius((d) => rScale(d.value))
                .angle((d, i) => i * angleSlice)
                .curve(d3.curveLinearClosed); // Add this line to close the polygon path

            chartGroup.selectAll('.radar-polygon')
                .data(processedData)
                .enter().append('path')
                .attr('class', 'radar-polygon')
                .attr('d', (d) => radarLine(d.axes))
                .style('fill', (d) => d.color)
                .style('fill-opacity', (d, i) => highlightedIndex === null || highlightedIndex === i ? 0.5 : 0.0)
                .style('stroke', 'black')
                .style('stroke-width', '1px');

            // Add axis labels
            const axisLabels = chartGroup.selectAll('.axis-label')
                .data(processedData[0].axes) // Updated from processedData[0].axes
                .enter().append('g')
                .attr('class', 'axis-label');

            // Add axis lines
            axisLabels.append('line')
                .attr('x1', 0)
                .attr('y1', 0)
                .attr('x2', (d, i) => rScale(0.7) * Math.cos(i * angleSlice - Math.PI / 2))
                .attr('y2', (d, i) => rScale(0.7) * Math.sin(i * angleSlice - Math.PI / 2))
                .style('stroke', '#cccccc')
                .style('stroke-width', '1px');

            axisLabels.append('text')
                .attr('x', (d, i) => (rScale(0.7) * Math.cos(i * angleSlice - Math.PI / 2)) + (Math.cos(i * angleSlice - Math.PI / 2) * 15))
                .attr('y', (d, i) => (rScale(0.7) * Math.sin(i * angleSlice - Math.PI / 2)) + (Math.sin(i * angleSlice - Math.PI / 2) * 15))
                .attr('dy', '.35em')
                .style('text-anchor', (d, i) => {
                    if (i < processedData[0].axes.length / 2) {
                        return 'start';
                    } else {
                        return 'end';
                    }
                })
                .style('font-size', '12px')
                .style('font-weight', 'bold') // Add this line to make the labels bold        
                .text((d) => d.axis);
        };

        draw();
    }, [processedData, width, height, highlightedIndex]);

    return (
        <svg ref={svgRef} width={width} height={height}></svg>
    );
};

export default SpiderChart;
