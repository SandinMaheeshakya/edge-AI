const employees = [
    { name: "John Doe", position: "Manager", health: ["Diabetes", "Hypertension"], oxygenLevels: [98, 97, 96, 95, 94], img: "https://i.pravatar.cc/80?img=1" },
    { name: "Jane Smith", position: "Developer", health: ["Asthma"], oxygenLevels: [99, 98, 97, 96, 95], img: "https://i.pravatar.cc/80?img=2" },
    { name: "Mark Taylor", position: "Designer", health: ["None"], oxygenLevels: [100, 99, 98, 97, 96], img: "https://i.pravatar.cc/80?img=3" },
    { name: "Lucy Brown", position: "HR", health: ["None"], oxygenLevels: [98, 97, 96, 96, 95], img: "https://i.pravatar.cc/80?img=4" },
    { name: "Oliver Green", position: "Accountant", health: ["Hypertension"], oxygenLevels: [96, 95, 94, 94, 93], img: "https://i.pravatar.cc/80?img=5" },
    { name: "Sophie White", position: "Marketing", health: ["None"], oxygenLevels: [99, 98, 97, 96, 95], img: "https://i.pravatar.cc/80?img=6" },
    { name: "Chris Black", position: "Sales", health: ["Asthma"], oxygenLevels: [97, 96, 95, 94, 93], img: "https://i.pravatar.cc/80?img=7" },
    { name: "Emma Blue", position: "Designer", health: ["None"], oxygenLevels: [100, 99, 98, 97, 96], img: "https://i.pravatar.cc/80?img=8" },
    { name: "Jack Red", position: "Developer", health: ["Allergy"], oxygenLevels: [95, 94, 93, 92, 91], img: "https://i.pravatar.cc/80?img=9" },
    { name: "Ella Purple", position: "Manager", health: ["None"], oxygenLevels: [98, 97, 96, 95, 94], img: "https://i.pravatar.cc/80?img=10" }
];


const container = document.getElementById("employeeContainer");

employees.forEach((emp, index) => {
    let card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
        <img src="${emp.img}" alt="${emp.name}">
        <h3>${emp.name}</h3>
        <p>${emp.position}</p>
        <div class="status">
            <div>
                <span>${emp.health.length}</span>
                <small>Health Issues</small>
            </div>
            <div>
                <span>Active</span>
                <small>Status</small>
            </div>
        </div>
    `;
    card.addEventListener("click", () => openModal(index));
    container.appendChild(card);
});

function openModal(index) {
    document.getElementById("empName").textContent = employees[index].name;
    document.getElementById("empPosition").textContent = employees[index].position;

    const healthList = document.getElementById("empHealth");
    healthList.innerHTML = "";
    employees[index].health.forEach(condition => {
        let li = document.createElement("li");
        li.textContent = condition;
        healthList.appendChild(li);
    });

    // Display Modal
    document.getElementById("employeeModal").classList.add("active");

    // Generate Oxygen Level Charts
    generateOxygenCharts(employees[index].oxygenLevels);
}

function closeModal() {
    document.getElementById("employeeModal").classList.remove("active");
}

function generateOxygenCharts(oxygenLevels) {
    // Destroy previous charts if they exist
    if (window.oxygenTrendsChart) {
        window.oxygenTrendsChart.destroy();
    }
    if (window.oxygenStatsChart) {
        window.oxygenStatsChart.destroy();
    }

    const ctx1 = document.getElementById("oxygen-trends").getContext("2d");
    window.oxygenTrendsChart = new Chart(ctx1, {
        type: "line",
        data: {
            labels: ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"],
            datasets: [{
                label: "Oxygen Level",
                data: oxygenLevels,
                borderColor: "blue",
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    const ctx2 = document.getElementById("oxygen-stats").getContext("2d");
    window.oxygenStatsChart = new Chart(ctx2, {
        type: "bar",
        data: {
            labels: ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5"],
            datasets: [{
                label: "Oxygen Level",
                data: oxygenLevels,
                backgroundColor: ["red", "orange", "yellow", "green", "blue"]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}


