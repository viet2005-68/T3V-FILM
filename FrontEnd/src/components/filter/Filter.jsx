import {useState} from "react";
import {MdTune} from "react-icons/md";
import {Button} from '@mui/material';
import "./filter.scss";

const filterOptions = {
    country: ["Tất cả", "Anh", "Mỹ", "Hàn Quốc", "Nhật Bản"],
    genre: ["Tất cả", "Hành động", "Tình cảm", "Kinh dị"],
    year: ["Tất cả", "2024", "2023", "2022"],
};

export default function Filter({onFilterApply}) {
    const [filters, setFilters] = useState({
        country: "Tất cả", genre: "Tất cả", year: "Tất cả",
    });
    const [showFilters, setShowFilters] = useState(false);

    const handleFilterChange = (type, value) => {
        setFilters((prev) => ({
            ...prev, [type]: value,
        }));
    };

    const handleApply = () => {
        if (onFilterApply) {
            onFilterApply(filters);
        }
    };

    return (<div className="filter">
        <div className="filter-toggle" onClick={() => setShowFilters(!showFilters)}>
            <MdTune size={20}/>
            <span>Bộ lọc</span>
        </div>

        <div className={`filter-elements ${showFilters ? "show" : ""}`}>
            {Object.entries(filterOptions).map(([type, options]) => (<div className="fe-row" key={type}>
                <div className="fe-name">
                    {type.charAt(0).toUpperCase() + type.slice(1)}:
                </div>
                <div className="fe-results">
                    {options.map((item) => (<div
                        key={item}
                        className={`item ${filters[type] === item ? "active-btn" : ""}`}
                        onClick={() => handleFilterChange(type, item)}
                    >
                        {item}
                    </div>))}
                </div>
            </div>))}

            <div style={{textAlign: "right", marginTop: "1rem"}}>
                <Button className='filter-btn'
                    variant="contained"
                    onClick={handleApply}
                    sx={{mr: 1}}
                >
                    Lọc
                </Button>

                <Button className='reset-btn'
                    variant="outlined"
                    onClick={() => setFilters({country: "Tất cả", genre: "Tất cả", year: "Tất cả"})}
                >
                    Reset
                </Button>
            </div>
        </div>
    </div>);
}
