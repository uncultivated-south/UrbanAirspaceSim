# UrbanAirspaceSim: A Simulation Framework for Congested Low-Altitude Airspace

## Vision
 
The rapid deployment of **Unmanned Aerial Vehicles (UAVs)**, **eVTOLs**, and other aerial mobility technologies will put significant pressure on cities' limited sky corridors.
In the near future, **urban low-altitude airspace will become increasingly congested**. 

Airspace, once considered an open and limitless environment, will transform into a **scarce and valuable resource**.  
Effective management of this resource is essential to ensure safety, fairness, and the sustainable growth of urban air mobility.

---

## Why an Economic Perspective?

As congestion grows, relying solely on technical pathfinding methods is insufficient.  
By treating **airspace as an economic resource**, we can:

- **Internalize scarcity**: Assign value to congested airspace segments.  
- **Enable multi-party interaction**: Encourage cooperation and negotiation between operators, regulators, and service providers.  
- **Optimize allocation**: Use market-inspired mechanisms such as auctions to achieve efficient global distribution of airspace slots.  

This project explores how **auction-based methods** can be combined with **conflict-based search (CBS)** in multi-agent pathfinding, creating a framework where **algorithmic optimization meets economic reasoning**.

---

# Airspace Resource Allocation System

## Overview
With the rapid development of the low-altitude economy, urban airspace will become increasingly crowded. Airspace, once considered limitless, may soon be treated as a scarce resource.  

This project proposes a **Python-based modular system** for rational allocation of low-altitude urban airspace.  

The system combines classical path planning (**A\***, **CBS**) with a market-based **auction mechanism** to resolve conflicts in airspace usage, ensuring fair and efficient allocation among multiple agents (aircraft).

---

## Core Concepts

### 1. Airspace Definition
- The airspace is represented as a **grid**.  
- States within the grid:
  - `#` → Static obstacles (e.g., buildings)  
  - `*` → Dynamic obstacles (e.g., assigned paths)  
  - `.` → Open airspace  
- **Note**: The occupancy/open state of each grid cell is **time-dependent**.

### 2. Agents
- Each aircraft is modeled as an **agent** with:
  - Unique **ID**  
  - Start position, destination, and current position  
  - Priority: **emergency** or **non-emergency**  
- Emergency agents are rare and handled with higher priority.

### 3. Emergency Agent Path Planning
- Emergency agents are assigned paths using **A\*** and **CBS (Conflict-Based Search)**.  
- Their planned paths are inserted into the airspace as **dynamic obstacles** (`*`).

### 4. General Path Planning
- **A\*** and **CBS** are used to check if the system can allocate paths to all agents under current constraints.  

### 5. Auction Mechanism (Triggered when CBS fails)
1. Collect conflict statistics to measure congestion in each grid.  
2. Generate a **heatmap of congestion**.  
3. Assign **starting prices** to each grid cell based on congestion.  
4. Broadcast the starting price set to all agents.  

### 6. Bidding Strategy for Agents
- Each agent is initialized with a **budget**, sampled from a random function and normal distribution.  
- Agents run **A\*** independently to generate a path.  
- The **total cost** of the path is calculated from grid starting prices.  
- If **total cost ≤ budget**:
  - The agent bids on the path.  
  - Bid for each grid cell = `budget / total cost * cell price`.  

### 7. Strategy Adjustment (If Over Budget)
- If **total cost > budget**:
  - The agent may **exit** with some probability.  
  - Or **adjust strategy**:
    - Re-run **A\*** treating the **highest-priced grid cell** as an obstacle.  
    - Recalculate total cost.  
    - Repeat by excluding the next highest-priced cells until:
      - A feasible path is found (≤ budget), or  
      - The agent exits the auction.  

### 8. Auction Result Analysis
- If an agent successfully acquires all grid cells in its path → **assign path**.  
- If multiple agents win paths:
  - Run **CBS** to check feasibility.  
  - If feasible → assign directly.  
  - If infeasible:
    - Keep the **highest bidder’s path**, add it as a dynamic obstacle.  
    - Re-check the next highest bidder with CBS.  
    - Repeat until conflicts are resolved.  

### 9. Iterative Auctions
- Return to **Step 5**.  
- Continue auctions until:
  - All agents have paths, OR  
  - No active bidders remain, OR  
  - Auction rounds exceed a defined maximum.  

---

## System Architecture
The system is **modularized** for clarity, maintainability, and extensibility:

- **Data Structures**
  - Unified representation for grids, agents, and obstacles.  
- **Algorithms**
  - Path planning: **A\*** and **CBS**  
  - Auction and pricing strategy  
  - Agent bidding and re-routing logic  
- **Interfaces**
  - Standardized I/O between modules  
  - Designed for future upgrades (e.g., RL-based strategies)  

---

## Key Features
- Combines **graph search algorithms** and **market-based mechanisms**  
- Supports **priority handling** (emergency vs non-emergency)  
- Generates **heatmap-based pricing model** for congestion  
- Enables **iterative resolution** of airspace conflicts  
- Designed with **scalability** and **modularity** in mind  

---

## Future Work
- Integration with real-world flight data  
- Visualization of airspace allocation & congestion heatmaps  
- Performance optimization for large-scale simulations  
- Extension to **3D airspace models**  

---

## Non-Commercial Use Only

**This project is released under the [CC BY-NC 4.0 License].**  
It is intended for **research, educational, and personal use only**.  
**Commercial use is strictly prohibited.**
