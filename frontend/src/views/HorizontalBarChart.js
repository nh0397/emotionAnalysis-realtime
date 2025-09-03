import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

function HorizontalBarChart({ data, yScale, transform }) {
    const svgRef = useRef(null);
    let tooltip = null;

    const showTooltip = (event, d, sentiment) => {
        if (!svgRef.current) return; // add null check to prevent error
        // const svgRect = svgRef.current.getBoundingClientRect();
        const xOffset = event.offsetX;
        const yOffset = event.offsetY - 40;
        const capitalizedSentiment = sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
        const tooltipContent =
            `${capitalizedSentiment}: ${Number(d['senti_' + sentiment + '_count']).toFixed(0)} tweets`;

        tooltip
            .style('opacity', 1)
            .style('left', Math.max(xOffset, 50) + 'px')
            .style('top', yOffset + 'px')
            .style('white-space', 'pre-wrap')
            .html(tooltipContent);
    };

    const enlargeBar = (event, d) => {
        d3.select(event.target)
            .attr('height', 15)
            .attr('y', (d) => yScale(d.state) + (yScale.bandwidth() - 14) / 2)
            .style('filter', 'saturate(200%)');;
    };

    const resetBar = (event) => {
        d3.select(event.target)
            .attr('height', 10)
            .attr('y', (d) => yScale(d.state) + (yScale.bandwidth() - 10) / 2)
            .style('filter', '');;
    };

    const hideTooltip = () => {
        tooltip.style('opacity', 0);
    };

    useEffect(() => {
        if (!data || data.length === 0) return;
        const svg = d3.select(svgRef.current);

        tooltip = d3.select('body')
            .append('tspan')
            .style('position', 'absolute')
            .style('background', '#fff2ed')
            .style('border', '1px solid #ccc')
            .style('padding', '5px')
            .style('cursor', 'pointer')
            .style('border-radius', '5px')
            .style('pointer-events', 'all')
            .style('opacity', 0);

        const dataWithSums = data.map(d => ({
            ...d,
            sum: parseInt(d.senti_neutral_count) + parseInt(d.senti_positive_count) + parseInt(d.senti_negative_count),
        }));

        const minSum = d3.min(dataWithSums, d => d.sum);
        const maxSum = d3.max(dataWithSums, d => d.sum);

        const widthScale = d3.scaleSqrt()
            .domain([0, maxSum])
            .range([30, 120]);

        const colors = {
            neutral: '#5C85FF',
            positive: '#85e085',
            negative: '#FF8080  ',
        };


        const startX = 0;
        const chartWidth = 220;

        ['neutral', 'positive', 'negative'].forEach((sentiment, index) => {
            svg.selectAll(`.bar-${sentiment}`)
                .data(dataWithSums)
                .join('rect')
                .attr('class', `bar-${sentiment}`)
                .attr('y', (d) => yScale(d.state) + (yScale.bandwidth() - 10) / 2)
                .attr('x', (d) => {
                    const prevSentiments = ['neutral', 'positive', 'negative'].slice(0, index);
                    const prevWidths = prevSentiments.map(s => widthScale(parseInt(d[`senti_${s}_count`])));
                    const xOffset = d3.sum(prevWidths);
                    const barWidth = widthScale(parseInt(d[`senti_${sentiment}_count`]));
                    return chartWidth - barWidth - xOffset + startX;
                })
                .attr('width', (d) => widthScale(parseInt(d[`senti_${sentiment}_count`])))
                .attr('height', 10)
                .attr('fill', colors[sentiment])
                .style('pointer-events', 'all') // Add this line
                .on('mouseover', (event, d) => {
                    showTooltip(event, d, sentiment);
                    enlargeBar(event, d);
                })
                .on('mousemove', (event, d) => showTooltip(event, d, sentiment))
                .on('mouseout', (event, d) => {
                    hideTooltip();
                    resetBar(event);
                });
        });

        return () => {
            tooltip.remove();
        };

    }, [data, yScale]);

    return (
        <>
            <g ref={svgRef} transform={transform}></g>
        </>
    );
};

export default HorizontalBarChart;

