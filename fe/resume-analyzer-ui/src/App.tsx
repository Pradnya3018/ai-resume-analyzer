import React, { useMemo, useState } from "react";
import jsPDF from "jspdf";

const BACKEND_API_URL =
  import.meta?.env?.VITE_BACKEND_API_URL || "http://localhost:8000";

function App() {
  const [activeTab, setActiveTab] = useState("intro");

  const [matchJobFile, setMatchJobFile] = useState(null);
  const [matchResumeFile, setMatchResumeFile] = useState(null);
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchError, setMatchError] = useState("");
  const [matchResult, setMatchResult] = useState(null);

  const [optimizeJobFile, setOptimizeJobFile] = useState(null);
  const [optimizeResumeFile, setOptimizeResumeFile] = useState(null);
  const [optimizeLoading, setOptimizeLoading] = useState(false);
  const [optimizeError, setOptimizeError] = useState("");
  const [optimizeResult, setOptimizeResult] = useState(null);

  async function postFiles(endpoint, jobFile, resumeFile, timeoutMs) {
    const formData = new FormData();
    formData.append("job_file", jobFile);
    formData.append("resume_file", resumeFile);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${BACKEND_API_URL}${endpoint}`, {
        method: "POST",
        body: formData,
        signal: controller.signal,
      });

      let data = null;
      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        throw new Error(data?.detail || `Request failed with status ${response.status}`);
      }

      return data;
    } catch (error) {
      if (error.name === "AbortError") {
        throw new Error("Backend took too long to respond. Try with a smaller resume PDF.");
      }

      if (error.message === "Failed to fetch") {
        throw new Error("Could not connect to backend. Please make sure backend is running.");
      }

      throw error;
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async function handleAnalyze() {
    setMatchError("");
    setMatchResult(null);

    if (!matchJobFile) {
      setMatchError("Please upload the job requirement file.");
      return;
    }

    if (!matchResumeFile) {
      setMatchError("Please upload the resume PDF.");
      return;
    }

    try {
      setMatchLoading(true);
      const result = await postFiles("/analyze", matchJobFile, matchResumeFile, 120000);
      setMatchResult(result);
    } catch (error) {
      setMatchError(error.message || "Unexpected error occurred.");
    } finally {
      setMatchLoading(false);
    }
  }

  async function handleOptimize() {
    setOptimizeError("");
    setOptimizeResult(null);

    if (!optimizeJobFile) {
      setOptimizeError("Please upload the job requirement file.");
      return;
    }

    if (!optimizeResumeFile) {
      setOptimizeError("Please upload the resume PDF.");
      return;
    }

    try {
      setOptimizeLoading(true);
      const result = await postFiles("/optimize", optimizeJobFile, optimizeResumeFile, 180000);
      setOptimizeResult(result);
    } catch (error) {
      setOptimizeError(error.message || "Unexpected error occurred.");
    } finally {
      setOptimizeLoading(false);
    }
  }

  function downloadOptimizedResume() {
    if (!optimizeResult?.optimized_resume) return;

    const doc = new jsPDF({
      orientation: "portrait",
      unit: "mm",
      format: "a4",
    });

    const marginLeft = 15;
    const marginTop = 18;
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const usableWidth = pageWidth - marginLeft * 2;
    const lineHeight = 7;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(11);

    const lines = doc.splitTextToSize(optimizeResult.optimized_resume, usableWidth);
    let y = marginTop;

    lines.forEach((line) => {
      if (y > pageHeight - marginTop) {
        doc.addPage();
        y = marginTop;
      }

      doc.text(line, marginLeft, y);
      y += lineHeight;
    });

    doc.save("optimized_resume.pdf");
  }

  return (
    <div className="app-shell">
      <style>{styles}</style>

      <header className="hero-card">
        <div>
          <p className="eyebrow">AI Resume Matching Tool</p>
          <h1>📄 Resume Analyzer AI</h1>
          <p className="hero-text">
            Compare a resume with a job requirement, calculate match percentage,
            identify skill gaps, and optimize resume wording responsibly.
          </p>
        </div>
      </header>

      <nav className="tabs">
        <TabButton
          label="Overview"
          active={activeTab === "intro"}
          onClick={() => setActiveTab("intro")}
        />
        <TabButton
          label="Match Score"
          active={activeTab === "match"}
          onClick={() => setActiveTab("match")}
        />
        <TabButton
          label="Resume Optimizer"
          active={activeTab === "optimize"}
          onClick={() => setActiveTab("optimize")}
        />
        <TabButton
          label="Resume Comparison"
          active={activeTab === "comparison"}
          onClick={() => setActiveTab("comparison")}
        />
      </nav>

      <main>
        {activeTab === "intro" && <IntroductionTab />}

        {activeTab === "match" && (
          <section className="panel">
            <h2>Resume Match Score</h2>
            <p className="muted">
              Upload the job requirement file and resume PDF to calculate the match percentage.
            </p>

            <UploadFilesSection
              jobFile={matchJobFile}
              resumeFile={matchResumeFile}
              onJobFileChange={setMatchJobFile}
              onResumeFileChange={setMatchResumeFile}
            />

            {matchError && <Alert type="error" message={matchError} />}

            <button
              className="primary-button"
              type="button"
              onClick={handleAnalyze}
              disabled={matchLoading}
            >
              {matchLoading ? "Analyzing resume..." : "Analyze Resume"}
            </button>

            {matchLoading && <Loader message="Analyzing resume..." />}
            {matchResult && <AnalyzeResult result={matchResult} />}
          </section>
        )}

        {activeTab === "optimize" && (
          <section className="panel">
            <h2>Resume Optimizer</h2>
            <p className="muted">
              Upload the job description and resume PDF. The AI will rewrite the resume to improve
              alignment with the job description while keeping the candidate's actual experience and
              projects unchanged.
            </p>

            <Alert
              type="warning"
              message="This tool can not create fake skill or fake experience."
            />

            <UploadFilesSection
              jobFile={optimizeJobFile}
              resumeFile={optimizeResumeFile}
              onJobFileChange={setOptimizeJobFile}
              onResumeFileChange={setOptimizeResumeFile}
            />

            {optimizeError && <Alert type="error" message={optimizeError} />}

            <button
              className="primary-button"
              type="button"
              onClick={handleOptimize}
              disabled={optimizeLoading}
            >
              {optimizeLoading ? "Optimizing resume..." : "Optimize Resume"}
            </button>

            {optimizeLoading && (
              <Loader message="Optimizing resume... This may take some time." />
            )}

            {optimizeResult && (
              <OptimizeResult
                result={optimizeResult}
                onDownload={downloadOptimizedResume}
              />
            )}
          </section>
        )}

        {activeTab === "comparison" && (
          <ComparisonTab optimizeResult={optimizeResult} />
        )}
      </main>
    </div>
  );
}

function TabButton({ label, active, onClick }) {
  return (
    <button
      type="button"
      className={`tab-button ${active ? "active" : ""}`}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

function IntroductionTab() {
  return (
    <section className="panel">
      <h2>Overview</h2>
      <p>
        This application helps compare a candidate resume with a job description. It uses an AI
        backend to analyze how closely the uploaded resume matches the technical skills and
        requirements mentioned in the job description.
      </p>

      <h3>Main Features</h3>
      <ol className="feature-list">
        <li>Upload a job requirement file containing technical skills.</li>
        <li>Upload a resume in PDF format.</li>
        <li>Calculate resume-to-job match percentage.</li>
        <li>Identify matched skills, partially matched skills, and missing skills.</li>
        <li>
          Optimize the resume based on the job description without changing the candidate's real
          experience.
        </li>
      </ol>

      <h3>Important Note</h3>
      <Alert
        type="warning"
        message="This tool can not create fake skill or fake experience. It can only improve wording, structure, and skill alignment based on the candidate's real resume."
      />
    </section>
  );
}

function UploadFilesSection({
  jobFile,
  resumeFile,
  onJobFileChange,
  onResumeFileChange,
}) {
  return (
    <div className="upload-grid">
      <FileInputCard
        label="Upload Job Requirement File"
        helperText="Accepted: TXT, CSV, PDF"
        accept=".txt,.csv,.pdf,text/plain,text/csv,application/pdf"
        file={jobFile}
        onChange={onJobFileChange}
      />

      <FileInputCard
        label="Upload Resume PDF"
        helperText="Accepted: PDF"
        accept=".pdf,application/pdf"
        file={resumeFile}
        onChange={onResumeFileChange}
      />
    </div>
  );
}

function FileInputCard({ label, helperText, accept, file, onChange }) {
  return (
    <label className="file-card">
      <span className="file-label">{label}</span>
      <span className="file-helper">{helperText}</span>
      <input
        type="file"
        accept={accept}
        onChange={(event) => onChange(event.target.files?.[0] || null)}
      />
      <span className="file-name">{file ? file.name : "No file selected"}</span>
    </label>
  );
}

function AnalyzeResult({ result }) {
  const finalScore = Number(result.final_match_percentage || 0);
  const llmScore = Number(result.llm_match_percentage || 0);
  const embeddingScore = Number(result.embedding_similarity_percentage || 0);

  return (
    <div className="result-block">
      <Alert type="success" message="Resume analysis completed." />

      <div className="metric-grid three">
        <MetricCard label="Final Match Percentage" value={`${finalScore}%`} />
        <MetricCard label="LLM Match Score" value={`${llmScore}%`} />
        <MetricCard label="Embedding Similarity" value={`${embeddingScore}%`} />
      </div>

      <ProgressBar value={finalScore} />

      <InfoSection title="Summary" content={result.summary} />
      <InfoSection title="Recommendation" content={result.recommendation} />

      <div className="skill-grid three">
        <SkillList title="Matched Skills" skills={result.matched_skills} />
        <SkillList title="Partially Matched Skills" skills={result.partially_matched_skills} />
        <SkillList title="Missing Skills" skills={result.missing_skills} />
      </div>
    </div>
  );
}

function OptimizeResult({ result, onDownload }) {
  return (
    <div className="result-block">
      <Alert type="success" message="Resume optimization completed." />

      <div className="metric-grid three">
        <MetricCard
          label="Original Match Percentage"
          value={`${result.original_match_percentage}%`}
        />
        <MetricCard
          label="Optimized Match Percentage"
          value={`${result.optimized_match_percentage}%`}
        />
        <MetricCard label="Improvement" value={`${result.improvement_percentage}%`} />
      </div>

      <InfoSection title="Changes Summary" content={result.changes_summary} />

      {result.warning && <Alert type="info" message={result.warning} />}

      <div className="skill-grid two">
        <SkillList
          title="Added or Improved Keywords"
          skills={result.added_or_improved_keywords}
        />
        <SkillList title="Keywords Not Added" skills={result.not_added_keywords} />
      </div>

      <div className="resume-output">
        <div className="section-heading-row">
          <h3>Optimized Resume</h3>
          <button type="button" className="secondary-button" onClick={onDownload}>
            Download Optimized Resume as PDF
          </button>
        </div>

        <textarea
          value={result.optimized_resume || ""}
          readOnly
          rows={24}
          aria-label="Optimized Resume Text"
        />
      </div>
    </div>
  );
}
function ComparisonTab({ optimizeResult }) {
  if (!optimizeResult) {
    return (
      <section className="panel">
        <h2>Resume Comparison</h2>
        <p className="muted">
          Optimize the resume first. After optimization, this tab will show the comparison between
          the original resume and optimized resume.
        </p>
        <Alert
          type="info"
          message="Go to Resume Optimizer, upload the job description and resume PDF, then click Optimize Resume."
        />
      </section>
    );
  }

  const comparisonRows = getTechnicalSkillComparisonRows(optimizeResult);

  return (
    <section className="panel">
      <h2>Resume Comparison</h2>
      <p className="muted">
        Compare technical skills between the original resume and optimized resume.
      </p>

      <TechnicalSkillComparisonChart skills={comparisonRows} />
    </section>
  );
}

function TechnicalSkillComparisonChart({ skills }) {
  if (!skills.length) {
    return (
      <div className="comparison-score-card">
        <h3>Technical Skills Comparison</h3>
        <p className="muted">
          No technical skills found for comparison. Make sure backend returns
          technical_skill_comparison in the optimize API response.
        </p>
      </div>
    );
  }

  const similarSkills = skills.filter(
    (item) =>
      item.status === "Present in Both" ||
      item.status === "Similar / Reworded"
  );

  const onlyOriginalSkills = skills.filter(
    (item) => item.status === "Only in Original"
  );

  const onlyOptimizedSkills = skills.filter(
    (item) => item.status === "Only in Optimized"
  );

  return (
    <div className="comparison-score-card">
      <h3>Technical Skills Comparison</h3>
      <p className="muted">
        This comparison shows how each technical skill from the original resume is represented in the optimized resume.
      </p>

      <div className="comparison-table-wrapper">
        <table className="comparison-table">
          <thead>
            <tr>
              <th>Skill</th>
              <th>Original Skill</th>
              <th>Optimized Skill</th>
              <th>Status</th>
              <th>Comparison</th>
            </tr>
          </thead>
          <tbody>
            {skills.map((item, index) => (
              <tr key={`${item.skill}-${index}`}>
                <td>{item.skill}</td>
                <td>{item.originalSkill || "-"}</td>
                <td>{item.optimizedSkill || "-"}</td>
                <td>
                  <span className={`status-badge ${getStatusClass(item.status)}`}>
                    {item.status}
                  </span>
                </td>
                <td>{item.comparison || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <h3>Skill Presence Chart</h3>

      <div className="skill-chart-legend">
        <span><i className="legend-dot original-dot" /> Original Resume</span>
        <span><i className="legend-dot optimized-dot" /> Optimized Resume</span>
      </div>

      <div className="skill-comparison-chart">
        {skills.map((item, index) => (
          <div className="skill-chart-row" key={`${item.skill}-chart-${index}`}>
            <div className="skill-chart-name">{item.skill}</div>

            <div className="skill-chart-bars">
              <div className="skill-bar-line">
                <span>Original</span>
                <div className="skill-bar-track">
                  <div
                    className={`skill-bar-fill original ${item.inOriginal ? "active" : "inactive"}`}
                    style={{ width: item.inOriginal ? "100%" : "8%" }}
                  />
                </div>
              </div>

              <div className="skill-bar-line">
                <span>Optimized</span>
                <div className="skill-bar-track">
                  <div
                    className={`skill-bar-fill optimized ${item.inOptimized ? "active" : "inactive"}`}
                    style={{ width: item.inOptimized ? "100%" : "8%" }}
                  />
                </div>
              </div>
            </div>

            <div className="skill-status-pill">
              {item.status}
            </div>
          </div>
        ))}
      </div>

      <div className="comparison-grid">
        <SkillComparisonList
          title="Similar / Matching Skills"
          rows={similarSkills}
        />

        <SkillComparisonList
          title="Skills Only in Original"
          rows={onlyOriginalSkills}
        />

        <SkillComparisonList
          title="Skills Only in Optimized"
          rows={onlyOptimizedSkills}
        />
      </div>
    </div>
  );
}
function getTechnicalSkillComparisonRows(optimizeResult) {
  const directRows = optimizeResult?.technical_skill_comparison || [];

  const nestedRows =
    optimizeResult?.comparison_data?.technical_skills?.skill_comparison || [];

  const rows = directRows.length ? directRows : nestedRows;

  if (Array.isArray(rows) && rows.length > 0) {
    return rows.map((row) => {
      const originalValue = Number(row.Original || row.original || 0);
      const optimizedValue = Number(row.Optimized || row.optimized || 0);

      return {
        skill: row.Skill || row.skill || "",
        originalSkill: row["Original Skill"] || row.original_skill || "",
        optimizedSkill: row["Optimized Skill"] || row.optimized_skill || "",
        inOriginal: originalValue > 0,
        inOptimized: optimizedValue > 0,
        status: row.Status || row.status || getSkillStatus(originalValue, optimizedValue),
        comparison: row.Comparison || row.comparison || "",
      };
    });
  }

  const originalSkills =
    optimizeResult.original_technical_skills ||
    optimizeResult.original_skills ||
    [];

  const optimizedSkills =
    optimizeResult.optimized_technical_skills ||
    optimizeResult.added_or_improved_keywords ||
    [];

  return buildTechnicalSkillComparison(originalSkills, optimizedSkills);
}


function getSkillStatus(originalValue, optimizedValue) {
  if (originalValue > 0 && optimizedValue > 0) {
    return "Present in Both";
  }

  if (originalValue > 0 && optimizedValue === 0) {
    return "Only in Original";
  }

  return "Only in Optimized";
}


function getStatusClass(status) {
  const normalizedStatus = String(status || "").toLowerCase();

  if (normalizedStatus.includes("both") || normalizedStatus.includes("similar")) {
    return "status-good";
  }

  if (normalizedStatus.includes("optimized")) {
    return "status-optimized";
  }

  if (normalizedStatus.includes("original")) {
    return "status-original";
  }

  return "status-neutral";
}


function SkillComparisonList({ title, rows }) {
  return (
    <div className="skill-card">
      <h3>{title}</h3>

      {!rows.length ? (
        <p className="muted">No data found.</p>
      ) : (
        <ul>
          {rows.map((row, index) => (
            <li key={`${row.skill}-${index}`}>
              <strong>{row.skill}</strong>
              <br />
              <span className="muted-text">
                {row.originalSkill || "-"} → {row.optimizedSkill || "-"}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function buildTechnicalSkillComparison(originalSkills, optimizedSkills) {
  const originalList = normalizeSkillList(originalSkills);
  const optimizedList = normalizeSkillList(optimizedSkills);
  const allSkills = [...originalList, ...optimizedList];
  const uniqueSkills = [];

  allSkills.forEach((skill) => {
    const exists = uniqueSkills.some(
      (existingSkill) => normalizeSkillName(existingSkill) === normalizeSkillName(skill)
    );

    if (!exists) {
      uniqueSkills.push(skill);
    }
  });

  return uniqueSkills.map((skill) => ({
    skill,
    inOriginal: originalList.some(
      (originalSkill) => normalizeSkillName(originalSkill) === normalizeSkillName(skill)
    ),
    inOptimized: optimizedList.some(
      (optimizedSkill) => normalizeSkillName(optimizedSkill) === normalizeSkillName(skill)
    ),
  }));
}

function normalizeSkillList(skills) {
  if (Array.isArray(skills)) {
    return skills
      .map((skill) => String(skill).trim())
      .filter(Boolean);
  }

  if (typeof skills === "string") {
    return skills
      .split(/[,|•]+/)
      .map((skill) => skill.trim())
      .filter(Boolean);
  }

  return [];
}

function normalizeSkillName(skill) {
  return String(skill)
    .toLowerCase()
    .replace(/[^a-z0-9+#.]/g, "")
    .trim();
}

function ComparisonCard({ title, content }) {
  return (
    <div className="comparison-card">
      <h3>{title}</h3>
      <p>{content}</p>
    </div>
  );
}

function extractSectionText(text, sectionNames) {
  if (!text) return "";

  const lines = text.split("\n");
  const normalizedSectionNames = sectionNames.map((name) => name.toLowerCase());
  let startIndex = -1;

  for (let index = 0; index < lines.length; index += 1) {
    const cleanLine = lines[index].replace(/[:#*\-]/g, "").trim().toLowerCase();

    if (normalizedSectionNames.some((sectionName) => cleanLine.includes(sectionName))) {
      startIndex = index + 1;
      break;
    }
  }

  if (startIndex === -1) return "";

  const sectionContent = [];

  for (let index = startIndex; index < lines.length; index += 1) {
    const line = lines[index];
    const cleanLine = line.replace(/[:#*\-]/g, "").trim();

    const looksLikeNextSection =
      cleanLine.length > 0 &&
      cleanLine.length < 45 &&
      cleanLine === cleanLine.toUpperCase();

    if (looksLikeNextSection) break;
    sectionContent.push(line);
  }

  return sectionContent.join("\n").trim();
}

function MetricCard({ label, value }) {
  return (
    <div className="metric-card">
      <p>{label}</p>
      <strong>{value}</strong>
    </div>
  );
}

function ProgressBar({ value }) {
  const safeValue = Math.max(0, Math.min(100, Number(value || 0)));

  return (
    <div className="progress-wrapper" aria-label={`Progress ${safeValue}%`}>
      <div className="progress-bar" style={{ width: `${safeValue}%` }} />
    </div>
  );
}

function InfoSection({ title, content }) {
  if (!content) return null;

  return (
    <div className="info-section">
      <h3>{title}</h3>
      <p>{content}</p>
    </div>
  );
}

function SkillList({ title, skills }) {
  const safeSkills = useMemo(() => (Array.isArray(skills) ? skills : []), [skills]);

  return (
    <div className="skill-card">
      <h3>{title}</h3>
      {safeSkills.length === 0 ? (
        <p className="muted">No data found.</p>
      ) : (
        <ul>
          {safeSkills.map((skill, index) => (
            <li key={`${skill}-${index}`}>{skill}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function Loader({ message }) {
  return (
    <div className="loader-row">
      <span className="spinner" />
      <span>{message}</span>
    </div>
  );
}

function Alert({ type, message }) {
  return <div className={`alert ${type}`}>{message}</div>;
}

const styles = `
  * {
    box-sizing: border-box;
  }

  html,
  body,
  #root {
    width: 100%;
    min-height: 100%;
    overflow-x: hidden;
  }

  body {
    margin: 0;
    min-height: 100vh;
    background:
      radial-gradient(circle at top left, rgba(37, 99, 235, 0.18), transparent 32%),
      radial-gradient(circle at top right, rgba(20, 184, 166, 0.14), transparent 30%),
      linear-gradient(135deg, #020617 0%, #0f172a 52%, #0b1120 100%);
    color: #e5e7eb;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }

  .app-shell {
    width: min(1480px, calc(100% - 64px));
    margin: 0 auto;
    padding: 24px 0 48px;
  }

  .hero-card,
  .panel {
    background: rgba(15, 23, 42, 0.9);
    border: none;
    border-radius: 22px;
    box-shadow: 0 22px 58px rgba(0, 0, 0, 0.34);
    backdrop-filter: blur(16px);
  }

  .hero-card {
    padding: 28px 32px;
    margin-bottom: 18px;
    position: relative;
    overflow: hidden;
    text-align: center;
  }

  .hero-card::after {
    content: "";
    position: absolute;
    width: 220px;
    height: 220px;
    right: -80px;
    top: -95px;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.28), transparent 68%);
    pointer-events: none;
  }

  .eyebrow {
    margin: 0 0 8px;
    color: #38bdf8;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.16em;
    text-transform: uppercase;
  }

  h1,
  h2,
  h3,
  p {
    margin-top: 0;
  }

  h1 {
    margin-bottom: 10px;
    color: #f8fafc;
    font-size: clamp(34px, 4vw, 46px);
    line-height: 1.08;
    letter-spacing: -0.03em;
  }

  h2 {
    margin-bottom: 10px;
    color: #f8fafc;
    font-size: 28px;
    line-height: 1.2;
    letter-spacing: -0.02em;
  }

  h3 {
    margin-bottom: 10px;
    color: #f8fafc;
    font-size: 17px;
    line-height: 1.3;
  }

  .hero-text,
  .muted,
  .panel p,
  .feature-list {
    color: #cbd5e1;
    line-height: 1.65;
    text-align: center;
  }

  .muted {
    font-size: 15.5px;
    line-height: 1.6;
  }

  .hero-text {
    max-width: 760px;
    margin: 0 auto;
    font-size: 16px;
  }

  .tabs {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin: 18px 0;
    padding: 8px;
    background: rgba(2, 6, 23, 0.55);
    border: none;
    border-radius: 20px;
  }

  .tab-button {
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 14px;
    background: rgba(15, 23, 42, 0.72);
    color: #cbd5e1;
    padding: 13px 14px;
    font-size: 15px;
    font-weight: 800;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .tab-button:hover {
    transform: translateY(-1px);
    border-color: rgba(56, 189, 248, 0.58);
    color: #f8fafc;
    background: rgba(30, 41, 59, 0.9);
  }

  .tab-button.active {
    border-color: rgba(56, 189, 248, 0.9);
    background: linear-gradient(135deg, #2563eb, #0891b2);
    color: #ffffff;
    box-shadow: 0 12px 26px rgba(37, 99, 235, 0.3);
  }

  .panel {
    padding: 28px 32px;
    text-align: center;
  }

  .panel > h2,
  .panel > p {
    max-width: 860px;
    margin-left: auto;
    margin-right: auto;
  }

  .feature-list {
    padding-left: 22px;
    max-width: 760px;
    margin-left: auto;
    margin-right: auto;
    text-align: left;
  }

  .upload-grid,
  .metric-grid,
  .skill-grid {
    display: grid;
    gap: 14px;
    margin: 20px 0;
  }

  .upload-grid,
  .skill-grid.two,
  .comparison-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .metric-grid.three,
  .skill-grid.three {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .file-card,
  .metric-card,
  .skill-card,
  .info-section,
  .resume-output,
  .comparison-score-card,
  .comparison-card {
    border: 1px solid rgba(148, 163, 184, 0.2);
    border-radius: 16px;
    background: rgba(2, 6, 23, 0.44);
    padding: 16px;
  }

  .file-card {
    display: flex;
    min-height: 135px;
    text-align: center;
    align-items: center;
    cursor: pointer;
    flex-direction: column;
    justify-content: center;
    gap: 7px;
    border-style: dashed;
    transition: all 0.2s ease;
  }

  .file-card:hover {
    border-color: rgba(56, 189, 248, 0.72);
    background: rgba(15, 23, 42, 0.82);
    transform: translateY(-1px);
  }

  .file-card input {
    margin-top: 6px;
    color: #cbd5e1;
  }

  .file-card input::file-selector-button {
    margin-right: 12px;
    border: 0;
    border-radius: 10px;
    background: #1d4ed8;
    color: #ffffff;
    padding: 8px 12px;
    font-weight: 800;
    cursor: pointer;
  }

  .file-label {
    color: #f8fafc;
    font-size: 15px;
    font-weight: 800;
  }

  .file-helper,
  .file-name {
    color: #94a3b8;
    font-size: 13px;
  }

  .file-name {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .primary-button,
  .secondary-button {
    border: 0;
    border-radius: 13px;
    cursor: pointer;
    font-weight: 800;
    transition: all 0.2s ease;
  }

  .primary-button {
    background: linear-gradient(135deg, #2563eb, #06b6d4);
    color: #ffffff;
    padding: 13px 20px;
    font-size: 15px;
    box-shadow: 0 12px 26px rgba(37, 99, 235, 0.28);
  }

  .secondary-button {
    background: rgba(30, 41, 59, 0.95);
    color: #f8fafc;
    padding: 10px 14px;
    font-size: 14px;
    border: 1px solid rgba(148, 163, 184, 0.28);
  }

  .primary-button:hover:not(:disabled),
  .secondary-button:hover:not(:disabled) {
    transform: translateY(-1px);
    filter: brightness(1.08);
  }

  .primary-button:disabled,
  .secondary-button:disabled {
    cursor: not-allowed;
    opacity: 0.7;
  }

  .loader-row {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-left: 12px;
    color: #cbd5e1;
    font-weight: 700;
  }

  .spinner {
    width: 18px;
    height: 18px;
    border: 3px solid rgba(59, 130, 246, 0.22);
    border-top-color: #38bdf8;
    border-radius: 999px;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .alert {
    margin: 14px 0;
    border-radius: 14px;
    padding: 13px 15px;
    line-height: 1.5;
    font-weight: 700;
    text-align: center;
  }

  .alert.warning {
    border: 1px solid rgba(251, 191, 36, 0.42);
    background: rgba(120, 53, 15, 0.28);
    color: #fde68a;
  }

  .alert.error {
    border: 1px solid rgba(248, 113, 113, 0.42);
    background: rgba(127, 29, 29, 0.34);
    color: #fecaca;
  }

  .alert.success {
    border: 1px solid rgba(74, 222, 128, 0.38);
    background: rgba(20, 83, 45, 0.32);
    color: #bbf7d0;
  }

  .alert.info {
    border: 1px solid rgba(96, 165, 250, 0.42);
    background: rgba(30, 64, 175, 0.28);
    color: #bfdbfe;
  }

  .result-block {
    margin-top: 22px;
  }

  .comparison-grid {
    display: grid;
    gap: 14px;
    margin: 20px 0;
  }

  .comparison-score-card {
    margin: 20px 0;
  }

  .comparison-card {
    min-height: 180px;
    text-align: center;
  }

  .comparison-card p {
    margin-bottom: 0;
    white-space: pre-wrap;
  }

  .skill-chart-legend {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin: 14px 0 18px;
    color: #cbd5e1;
    font-size: 14px;
    font-weight: 800;
  }

  .skill-chart-legend span {
    display: inline-flex;
    align-items: center;
    gap: 8px;
  }

  .legend-dot {
    width: 10px;
    height: 10px;
    border-radius: 999px;
    display: inline-block;
  }

  .original-dot {
    background: #38bdf8;
  }

  .optimized-dot {
    background: #22c55e;
  }

  .skill-comparison-chart {
    display: grid;
    gap: 14px;
    margin-top: 10px;
  }

  .skill-chart-row {
    display: grid;
    grid-template-columns: 180px 1fr 150px;
    gap: 14px;
    align-items: center;
    padding: 14px;
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 14px;
    background: rgba(15, 23, 42, 0.52);
  }

  .skill-chart-name {
    color: #f8fafc;
    font-weight: 900;
    text-align: left;
    word-break: break-word;
  }

  .skill-chart-bars {
    display: grid;
    gap: 8px;
  }

  .skill-bar-line {
    display: grid;
    grid-template-columns: 80px 1fr;
    gap: 10px;
    align-items: center;
    color: #94a3b8;
    font-size: 13px;
    font-weight: 800;
    text-align: left;
  }

  .skill-bar-track {
    height: 12px;
    overflow: hidden;
    border-radius: 999px;
    background: rgba(51, 65, 85, 0.86);
  }

  .skill-bar-fill {
    height: 100%;
    border-radius: inherit;
    transition: width 0.35s ease;
  }

  .skill-bar-fill.original.active {
    background: #38bdf8;
  }

  .skill-bar-fill.optimized.active {
    background: #22c55e;
  }

  .skill-bar-fill.inactive {
    background: rgba(148, 163, 184, 0.35);
  }

  .skill-status-pill {
    justify-self: end;
    border: 1px solid rgba(148, 163, 184, 0.24);
    border-radius: 999px;
    padding: 7px 10px;
    color: #e5e7eb;
    background: rgba(2, 6, 23, 0.5);
    font-size: 12px;
    font-weight: 900;
    white-space: nowrap;
  }

  .metric-card {
    background: linear-gradient(180deg, rgba(15, 23, 42, 0.86), rgba(2, 6, 23, 0.42));
    text-align: center;
  }

  .metric-card p {
    margin-bottom: 8px;
    color: #94a3b8;
    font-size: 13px;
    font-weight: 800;
  }

  .metric-card strong {
    color: #f8fafc;
    font-size: 30px;
    line-height: 1;
  }

  .progress-wrapper {
    width: 100%;
    height: 16px;
    margin: 10px 0 24px;
    overflow: hidden;
    border-radius: 999px;
    background: rgba(51, 65, 85, 0.8);
  }

  .progress-bar {
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(90deg, #38bdf8, #22c55e);
    transition: width 0.35s ease;
  }

  .info-section {
    margin-bottom: 14px;
    text-align: center;
  }

  .info-section p {
    margin-bottom: 0;
  }

  .skill-card {
    text-align: center;
  }

  .skill-card ul {
    display: inline-block;
    margin: 0;
    padding-left: 20px;
    text-align: left;
    color: #dbeafe;
    line-height: 1.75;
  }

  .skill-card li::marker {
    color: #38bdf8;
  }

  @media (max-width: 860px) {
    .skill-chart-row {
      grid-template-columns: 1fr;
      text-align: center;
    }

    .skill-chart-name {
      text-align: center;
    }

    .skill-status-pill {
      justify-self: center;
    }
  }

  .section-heading-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    margin-bottom: 12px;
  }

  .section-heading-row h3 {
    margin-bottom: 0;
  }

  textarea {
    width: 100%;
    min-height: 520px;
    resize: vertical;
    border: 1px solid rgba(148, 163, 184, 0.28);
    border-radius: 16px;
    padding: 16px;
    color: #e5e7eb;
    background: rgba(2, 6, 23, 0.76);
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
    font-size: 14px;
    line-height: 1.6;
    outline: none;
  }

  textarea:focus {
    border-color: rgba(56, 189, 248, 0.85);
    box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.14);
  }

  @media (max-width: 860px) {
  .app-shell {
    width: min(100% - 28px, 1480px);
    padding-top: 18px;
  }

  .tabs,
  .upload-grid,
  .metric-grid.three,
  .skill-grid.three,
  .skill-grid.two,
  .comparison-grid {
    grid-template-columns: 1fr;
  }

  .panel,
  .hero-card {
    padding: 22px;
  }

  .loader-row {
    display: flex;
    margin: 14px 0 0;
  }

  .section-heading-row {
    align-items: stretch;
    flex-direction: column;
  }
}

/* Comparison table styles should be outside media block */

.comparison-table-wrapper {
  width: 100%;
  margin: 18px 0 28px;
  overflow-x: auto;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 16px;
  background: rgba(2, 6, 23, 0.44);
}

.comparison-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 920px;
  text-align: left;
}

.comparison-table th,
.comparison-table td {
  padding: 13px 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.16);
  color: #dbeafe;
  vertical-align: top;
  font-size: 13px;
  line-height: 1.45;
}

.comparison-table th {
  color: #f8fafc;
  background: rgba(15, 23, 42, 0.9);
  font-weight: 900;
}

.comparison-table tr:last-child td {
  border-bottom: none;
}

.status-badge {
  display: inline-block;
  min-width: 120px;
  border-radius: 999px;
  padding: 6px 9px;
  text-align: center;
  font-size: 11px;
  font-weight: 900;
  white-space: nowrap;
}

.status-good {
  border: 1px solid rgba(34, 197, 94, 0.42);
  background: rgba(20, 83, 45, 0.35);
  color: #bbf7d0;
}

.status-optimized {
  border: 1px solid rgba(56, 189, 248, 0.42);
  background: rgba(12, 74, 110, 0.35);
  color: #bae6fd;
}

.status-original {
  border: 1px solid rgba(251, 191, 36, 0.42);
  background: rgba(120, 53, 15, 0.35);
  color: #fde68a;
}

.status-neutral {
  border: 1px solid rgba(148, 163, 184, 0.34);
  background: rgba(30, 41, 59, 0.5);
  color: #e5e7eb;
}

.muted-text {
  color: #94a3b8;
  font-size: 13px;
}
`;

export default App;
