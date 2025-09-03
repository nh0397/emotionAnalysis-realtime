import React, { useEffect } from 'react';
import Select from 'react-select';
import './StateFilterCheckboxes.css';


const StateFilterCheckboxes = ({ states, onStateSelection, transform }) => {
    const [selectedStates, setSelectedStates] = React.useState([]);

    useEffect(() => {
        setSelectedStates(states.map(state => ({ value: state, label: state })));
    }, [states]);

    const handleChange = (selected) => {
        const selectedValues = selected.map(option => option.value);
        const remainingStates = states.filter(state => !selectedValues.includes(state));
        setSelectedStates(remainingStates.map(state => ({ value: state, label: state })));
        if (onStateSelection) {
            onStateSelection(selectedValues);
        }
    };


    return (
        <foreignObject transform={transform} width="350" height="250">
            <div className="state-filter-checkboxes">
                <Select
                    options={selectedStates}
                    isMulti={true}
                    onChange={handleChange}
                    className="state-select"
                    placeholder="Select States"
                    menuIsOpen={true}
                />
            </div>
        </foreignObject>
    );
};

export default StateFilterCheckboxes;

