window.updateDetailsPanelForLocation = function(location, getEpisodesForLocation) {
  const panel = document.getElementById("details-panel");
  if (!panel) return;

  let artifactsHtml = "";
  if (location.artifacts && location.artifacts.length > 0) {
    const items = location.artifacts
      .map(art => {
        const epText =
          art.episode_season && art.episode_number
            ? `S${art.episode_season}E${art.episode_number} – ${art.episode_title || ""}`
            : "Episode unknown";

        return `
          <li>
            <strong>${art.name}</strong><br>
            <span class="details-meta">${epText}</span><br>
            <span>${art.description || ""}</span>
            ${
              art.depth_m
                ? `<br><span class="details-meta">Depth: ${art.depth_m} m</span>`
                : ""
            }
          </li>
        `;
      })
      .join("");

    artifactsHtml = `
      <div class="details-artifacts">
        <h4>Artifacts (${location.artifacts.length})</h4>
        <ul>${items}</ul>
      </div>
    `;
  }

  const episodes = getEpisodesForLocation(location);
  const episodesHtml = episodes.length
    ? `
      <div class="details-episodes">
        <h4>Episodes</h4>
        <ul>
          ${episodes
            .map(
              ep =>
                `<li class="episode-link" data-season="${ep.season}" data-episode="${ep.episode}">S${ep.season}E${ep.episode} – ${ep.title || ""}</li>`
            )
            .join("")}
        </ul>
      </div>
    `
    : "";

  const seasonsText =
    location.relatedSeasons && location.relatedSeasons.length > 0
      ? location.relatedSeasons.map(s => `S${s}`).join(", ")
      : "Not specified";

  panel.innerHTML = `
    <div>
      <h3>${location.name}</h3>
      <div class="details-meta">
        <span>Type: ${location.type}</span><br>
        ${
          location.firstDocumentedYear
            ? `<span>First documented: ${location.firstDocumentedYear}</span><br>`
            : ""
        }
        <span>Appears in: ${seasonsText}</span>
      </div>
      <p>${location.description || ""}</p>
      ${artifactsHtml}
      ${episodesHtml}
    </div>
  `;

  // Add click handlers for episode links
  const episodeLinks = panel.querySelectorAll('.episode-link');
  episodeLinks.forEach(link => {
    link.addEventListener('click', () => {
      const season = parseInt(link.dataset.season);
      const episode = parseInt(link.dataset.episode);
      window.highlightLocationsForEpisode(season, episode);
    });
  });
};

window.updateDetailsPanelForBorehole = function(bh, loc) {
  const panel = document.getElementById("details-panel");
  if (!panel) return;

  panel.innerHTML = `
    <div>
      <h3>${bh.name}</h3>
      <div class="details-meta">
        <span>Borehole ID: ${bh.borehole_id}</span><br>
        <span>Location: ${loc ? loc.name : bh.location_id}</span><br>
        <span>Intervals: ${bh.intervals.length}</span>
      </div>
    </div>
  `;
};

window.updateDetailsPanelForArtifact = function(art, loc) {
  const panel = document.getElementById("details-panel");
  if (!panel) return;

  const epText =
    art.episode_season && art.episode_number
      ? `S${art.episode_season}E${art.episode_number} – ${art.episode_title || ""}`
      : "Episode unknown";

  panel.innerHTML = `
    <div>
      <h3>${art.name}</h3>
      <div class="details-meta">
        <span>Location: ${loc ? loc.name : art.location_id}</span><br>
        <span>${epText}</span><br>
        ${
          art.depth_m
            ? `<span>Depth: ${art.depth_m} m</span><br>`
            : ""
        }
      </div>
      <p>${art.description || ""}</p>
    </div>
  `;
};

window.renderCrossSectionForLocation = function(location) {
  const container = document.getElementById("cross-section");
  if (!container) return;

  container.innerHTML = "";

  const intervals = location.intervals || [];
  const artifacts = location.artifacts || [];
  
  if (!intervals.length && !artifacts.length) {
    container.innerHTML = `<p class="details-meta">No depth data available for this location.</p>`;
    return;
  }

  window.renderCrossSection({ intervals, artifacts, title: location.name });
};

window.renderCrossSectionForBorehole = function(bh) {
  const container = document.getElementById("cross-section");
  if (!container) return;

  container.innerHTML = "";

  const intervals = bh.intervals || [];
  const artifacts = []; // Boreholes don't have artifacts directly
  
  if (!intervals.length) {
    container.innerHTML = `<p class="details-meta">No depth data available for this borehole.</p>`;
    return;
  }

  window.renderCrossSection({ intervals, artifacts, title: bh.name });
};

window.renderCrossSection = function(obj) {
  const container = document.getElementById("cross-section");
  if (!container) return;

  container.innerHTML = "";

  const intervals = obj.intervals || [];
  const artifacts = obj.artifacts || [];
  const title = obj.title || "Cross-Section";

  // Calculate depth range
  let maxDepth = 0;
  if (intervals.length > 0) {
    maxDepth = Math.max(
      ...intervals.map(i => parseFloat(i.depth_to || i.depthTo || 0))
    );
  }
  if (artifacts.length > 0) {
    maxDepth = Math.max(maxDepth, 
      ...artifacts.map(a => parseFloat(a.depth_m || 0))
    );
  }

  if (maxDepth <= 0) {
    container.innerHTML = `<p class="details-meta">No depth data available.</p>`;
    return;
  }

  const width = 200;
  const height = 350;
  const padding = 20;
  const legendWidth = 80;

  const svgNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("width", width + legendWidth);
  svg.setAttribute("height", height);
  svg.setAttribute("viewBox", `0 0 ${width + legendWidth} ${height}`);
  svg.style.background = "#1f2937";
  svg.style.borderRadius = "8px";

  const scaleY = depth =>
    padding + (depth / maxDepth) * (height - 2 * padding);

  // Enhanced material color function
  const materialColor = materialRaw => {
    const m = window.normalizeString(materialRaw);
    if (m.includes("wood") || m.includes("timber")) return "#92400e";
    if (m.includes("clay") || m.includes("mud")) return "#1e40af";
    if (m.includes("void") || m.includes("cavity") || m.includes("air")) return "#7c3aed";
    if (m.includes("metal") || m.includes("iron")) return "#6b7280";
    if (m.includes("sand") || m.includes("soil")) return "#d97706";
    if (m.includes("stone") || m.includes("rock")) return "#374151";
    if (m.includes("water")) return "#0891b2";
    if (m.includes("coal") || m.includes("charcoal")) return "#1f2937";
    return "#4b5563"; // default gray
  };

  // Artifact color function
  const artifactColor = category => {
    const c = window.normalizeString(category || "");
    if (c.includes("coin") || c.includes("gold")) return "#fbbf24";
    if (c.includes("tool") || c.includes("metal")) return "#9ca3af";
    if (c.includes("wood")) return "#92400e";
    if (c.includes("stone")) return "#6b7280";
    return "#ef4444"; // default red for artifacts
  };

  // Draw intervals (geological layers)
  intervals.forEach(interval => {
    const from = parseFloat(interval.depth_from || interval.depthFrom || 0);
    const to = parseFloat(interval.depth_to || interval.depthTo || 0);
    const material = interval.material || "";

    const y1 = scaleY(from);
    const y2 = scaleY(to);
    const rectHeight = Math.max(1, y2 - y1);

    const rect = document.createElementNS(svgNS, "rect");
    rect.setAttribute("x", legendWidth + 10);
    rect.setAttribute("y", y1);
    rect.setAttribute("width", width - legendWidth - 20);
    rect.setAttribute("height", rectHeight);
    rect.setAttribute("fill", materialColor(material));
    rect.setAttribute("stroke", "#374151");
    rect.setAttribute("stroke-width", "0.5");
    rect.setAttribute("data-depth", `${from}-${to}`);
    rect.setAttribute("data-material", material);
    
    // Add tooltip
    rect.setAttribute("title", `${material} (${from}m - ${to}m)`);
    
    // Make interactive
    rect.addEventListener("click", () => {
      showDepthDetails(from, to, material, null);
    });
    
    svg.appendChild(rect);
  });

  // Draw artifact markers
  artifacts.forEach(artifact => {
    const depth = parseFloat(artifact.depth_m || 0);
    if (depth <= 0) return;

    const y = scaleY(depth);
    const color = artifactColor(artifact.category);

    // Draw artifact marker (triangle or diamond)
    const marker = document.createElementNS(svgNS, "polygon");
    marker.setAttribute("points", `${legendWidth + 15},${y} ${legendWidth + 25},${y-5} ${legendWidth + 35},${y} ${legendWidth + 25},${y+5}`);
    marker.setAttribute("fill", color);
    marker.setAttribute("stroke", "#000");
    marker.setAttribute("stroke-width", "1");
    marker.setAttribute("data-artifact", artifact.name);
    marker.setAttribute("data-depth", depth);
    
    // Add tooltip
    marker.setAttribute("title", `${artifact.name} (${depth}m) - ${artifact.description || ""}`);
    
    // Make interactive
    marker.addEventListener("click", () => {
      showDepthDetails(depth, depth, null, artifact);
    });
    
    svg.appendChild(marker);
  });

  // Draw depth axis
  const axis = document.createElementNS(svgNS, "line");
  axis.setAttribute("x1", legendWidth + 5);
  axis.setAttribute("y1", padding);
  axis.setAttribute("x2", legendWidth + 5);
  axis.setAttribute("y2", height - padding);
  axis.setAttribute("stroke", "#9ca3af");
  axis.setAttribute("stroke-width", "2");
  svg.appendChild(axis);

  // Depth labels
  const topLabel = document.createElementNS(svgNS, "text");
  topLabel.setAttribute("x", legendWidth);
  topLabel.setAttribute("y", padding + 5);
  topLabel.setAttribute("fill", "#e5e7eb");
  topLabel.setAttribute("font-size", "10");
  topLabel.setAttribute("text-anchor", "end");
  topLabel.textContent = "0 m";
  svg.appendChild(topLabel);

  const bottomLabel = document.createElementNS(svgNS, "text");
  bottomLabel.setAttribute("x", legendWidth);
  bottomLabel.setAttribute("y", height - padding + 5);
  bottomLabel.setAttribute("fill", "#e5e7eb");
  bottomLabel.setAttribute("font-size", "10");
  bottomLabel.setAttribute("text-anchor", "end");
  bottomLabel.textContent = `${maxDepth.toFixed(1)} m`;
  svg.appendChild(bottomLabel);

  // Title
  const titleText = document.createElementNS(svgNS, "text");
  titleText.setAttribute("x", (width + legendWidth) / 2);
  titleText.setAttribute("y", 15);
  titleText.setAttribute("fill", "#e5e7eb");
  titleText.setAttribute("font-size", "12");
  titleText.setAttribute("font-weight", "bold");
  titleText.setAttribute("text-anchor", "middle");
  titleText.textContent = title;
  svg.appendChild(titleText);

  // Create legend
  const legendY = padding + 30;
  const legendItems = [
    { material: "Wood/Timber", color: "#92400e" },
    { material: "Clay/Mud", color: "#1e40af" },
    { material: "Void/Cavity", color: "#7c3aed" },
    { material: "Sand/Soil", color: "#d97706" },
    { material: "Stone/Rock", color: "#374151" },
    { material: "Metal", color: "#6b7280" },
    { material: "Artifacts", color: "#ef4444", shape: "diamond" }
  ];

  legendItems.forEach((item, index) => {
    const y = legendY + index * 15;
    
    // Color swatch
    const swatch = document.createElementNS(svgNS, "rect");
    swatch.setAttribute("x", 5);
    swatch.setAttribute("y", y - 8);
    swatch.setAttribute("width", 12);
    swatch.setAttribute("height", 12);
    swatch.setAttribute("fill", item.color);
    swatch.setAttribute("stroke", "#374151");
    swatch.setAttribute("stroke-width", "1");
    svg.appendChild(swatch);
    
    // Label
    const label = document.createElementNS(svgNS, "text");
    label.setAttribute("x", 22);
    label.setAttribute("y", y);
    label.setAttribute("fill", "#e5e7eb");
    label.setAttribute("font-size", "9");
    label.textContent = item.material;
    svg.appendChild(label);
  });

  container.appendChild(svg);

  // Add depth details panel
  const detailsDiv = document.createElement("div");
  detailsDiv.id = "depth-details";
  detailsDiv.style.marginTop = "10px";
  detailsDiv.style.padding = "8px";
  detailsDiv.style.background = "#374151";
  detailsDiv.style.borderRadius = "4px";
  detailsDiv.style.fontSize = "12px";
  detailsDiv.style.color = "#e5e7eb";
  detailsDiv.innerHTML = "<em>Click on layers or artifacts for details</em>";
  container.appendChild(detailsDiv);
};

// Helper function to show depth details
function showDepthDetails(fromDepth, toDepth, material, artifact) {
  const detailsDiv = document.getElementById("depth-details");
  if (!detailsDiv) return;

  if (artifact) {
    detailsDiv.innerHTML = `
      <strong>${artifact.name}</strong><br>
      Depth: ${fromDepth.toFixed(1)} m<br>
      Category: ${artifact.category || "Unknown"}<br>
      ${artifact.description ? `Description: ${artifact.description}<br>` : ""}
      ${artifact.episode_season && artifact.episode_number ? 
        `Found in: Season ${artifact.episode_season}, Episode ${artifact.episode_number}` : ""}
    `;
  } else {
    detailsDiv.innerHTML = `
      <strong>Geological Layer</strong><br>
      Depth: ${fromDepth.toFixed(1)} - ${toDepth.toFixed(1)} m<br>
      Material: ${material || "Unknown"}<br>
      Thickness: ${(toDepth - fromDepth).toFixed(1)} m
    `;
  }
}
