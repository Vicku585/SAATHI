/* =====================================================
   API CONFIGURATION
===================================================== */

const API_URL =
    window.location.protocol === "file:"
        ? "http://127.0.0.1:8000"
        : window.location.origin;

const TOKEN_KEY = "sentinels_access_token";
const USER_KEY = "sentinels_user";


/*
    Existing database personnel.

    Database ID: 1
    Personnel: Test Personnel / P1001

    This remains prototype context for the current demo.
    In the final architecture, personnel identity should come
    from the authenticated user/session rather than a manually
    entered Personnel ID.
*/

const PERSONNEL_DB_ID = 1;


/* =====================================================
   AUTHENTICATION
===================================================== */

function getAccessToken() {
    return sessionStorage.getItem(TOKEN_KEY);
}


function getCurrentUser() {
    const rawUser = sessionStorage.getItem(USER_KEY);

    if (!rawUser) {
        return null;
    }

    try {
        return JSON.parse(rawUser);
    }
    catch (error) {
        return null;
    }
}


/*
    Add the JWT token automatically to protected API requests.
*/

async function authFetch(url, options = {}) {

    const token = getAccessToken();

    if (!token) {
        showLoginScreen();
        throw new Error("Authentication required.");
    }

    const headers = new Headers(
        options.headers || {}
    );

    headers.set(
        "Authorization",
        `Bearer ${token}`
    );

    if (
        options.body &&
        !headers.has("Content-Type")
    ) {
        headers.set(
            "Content-Type",
            "application/json"
        );
    }

    const response = await fetch(
        url,
        {
            ...options,
            headers: headers
        }
    );

    /*
        Token expired or became invalid.
        Return the user to the login screen.
    */

    if (response.status === 401) {
        logout(
            "Your session has expired. Please sign in again."
        );

        throw new Error(
            "Authentication session expired."
        );
    }

    return response;
}


/* =====================================================
   LOGIN
===================================================== */

async function login() {

    const username = document.getElementById("loginUsername").value.trim();
    const password = document.getElementById("loginPassword").value;
    const errorBox = document.getElementById("loginError");
    const loginButton = document.getElementById("loginSubmitButton");

    errorBox.style.display = "none";
    errorBox.textContent = "";

    if (!username || !password) {
        errorBox.textContent = "Please enter username and password.";
        errorBox.style.display = "block";
        return;
    }

    if (loginButton) {
        loginButton.disabled = true;
        loginButton.classList.add("is-loading");
        const label = loginButton.querySelector("span:first-child");
        if (label) label.textContent = "Signing in...";
    }

    try {
        /*
            Start every login from a clean client-side state.
            This prevents a previous user's active page from
            appearing during role switching.
        */
        resetApplicationView();

        const response = await fetch(
            `${API_URL}/auth/login`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            }
        );

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.message || "Login failed.");
        }

        sessionStorage.setItem(TOKEN_KEY, data.access_token);
        sessionStorage.setItem(USER_KEY, JSON.stringify(data.user));

        showApplication(data.user);

    } catch (error) {

        console.error(error);

        errorBox.textContent =
            error.message || "Unable to sign in.";

        errorBox.style.display = "block";

    } finally {

        if (loginButton) {
            loginButton.disabled = false;
            loginButton.classList.remove("is-loading");
            const label = loginButton.querySelector("span:first-child");
            if (label) label.textContent = "Sign in securely";
        }
    }
}


/* =====================================================
   SHOW APPLICATION
===================================================== */

function showApplication(user) {

    /*
        Always establish a clean application state for the new user.
        This is important when switching roles in the same browser
        session (welfare officer → logout → personnel).
    */
    resetApplicationView();

    const appShell = document.getElementById("appShell");

    if (appShell) {
        appShell.dataset.role = user.role || "";
        appShell.classList.remove("mobile-nav-open");
    }

    document.getElementById("loginScreen").style.display = "none";
    document.getElementById("appShell").style.display = "block";

    const sessionUser = document.getElementById("sessionUser");
    if (sessionUser) {
        sessionUser.textContent = user.username || "Authenticated user";
    }

    const sessionRole = document.getElementById("sessionRole");

    if (sessionRole) {
        const roleLabels = {
            personnel: "Personnel",
            welfare_officer: "Welfare Officer",
            commander: "Commander",
            admin: "Administrator"
        };

        sessionRole.textContent =
            roleLabels[user.role] || user.role || "User";
    }

    const dashboardButton =
        document.getElementById("dashboardNavButton");

    const commanderButton =
        document.getElementById("commanderNavButton");

    if (dashboardButton) {
        const dashboardAllowed =
            user.role === "admin" || user.role === "welfare_officer";

        dashboardButton.style.display =
            dashboardAllowed ? "inline-flex" : "none";
    }

    if (commanderButton) {
        const commanderAllowed =
            user.role === "admin" || user.role === "commander";

        commanderButton.style.display =
            commanderAllowed ? "inline-flex" : "none";
    }

    const operationalSection =
        document.getElementById("operationalSection");

    const personnelOperationalNotice =
        document.getElementById("personnelOperationalNotice");

    if (operationalSection) {
        operationalSection.style.display =
            user.role === "personnel" ? "none" : "block";
    }

    if (personnelOperationalNotice) {
        personnelOperationalNotice.style.display =
            user.role === "personnel" ? "block" : "none";
    }

    applyRolePresentation(user);
}


/* =====================================================
   SHOW LOGIN SCREEN
===================================================== */

function resetApplicationView() {

    document.querySelectorAll(".page").forEach(page => {
        page.classList.remove("active");
    });

    document.querySelectorAll(".nav-btn").forEach(button => {
        button.classList.remove("active");
    });

    const assessmentPage = document.getElementById("assessment");
    const assessmentButton = document.getElementById("assessmentNavButton");

    if (assessmentPage) assessmentPage.classList.add("active");
    if (assessmentButton) assessmentButton.classList.add("active");

    const result = document.getElementById("result");
    if (result) {
        result.style.display = "none";
        result.className = "";
        result.innerHTML = "";
    }

    const caseDetails = document.getElementById("caseDetails");
    if (caseDetails) caseDetails.style.display = "none";

    const caseDetailsContent =
        document.getElementById("caseDetailsContent");

    if (caseDetailsContent) caseDetailsContent.innerHTML = "";

    const appShell = document.getElementById("appShell");
    if (appShell) appShell.classList.remove("mobile-nav-open");

    if (typeof activeWelfareCase !== "undefined") {
        activeWelfareCase = null;
    }

    if (typeof activeFollowUps !== "undefined") {
        activeFollowUps = [];
    }
}


function showLoginScreen() {

    resetApplicationView();

    const appShell = document.getElementById("appShell");

    if (appShell) {
        appShell.style.display = "none";
        appShell.dataset.role = "";
        appShell.classList.remove("mobile-nav-open");
    }

    const loginScreen = document.getElementById("loginScreen");

    if (loginScreen) loginScreen.style.display = "flex";
}


function logout(message = "") {

    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);

    resetApplicationView();

    const usernameInput = document.getElementById("loginUsername");
    const passwordInput = document.getElementById("loginPassword");

    if (usernameInput) usernameInput.value = "";
    if (passwordInput) passwordInput.value = "";

    showLoginScreen();

    if (message) {
        const errorBox = document.getElementById("loginError");
        errorBox.textContent = message;
        errorBox.style.display = "block";
    }
}


/* =====================================================
   SESSION INITIALIZATION
===================================================== */

function initializeSession() {

    const token =
        getAccessToken();

    const user =
        getCurrentUser();

    if (token && user) {

        showApplication(user);

    }
    else {

        showLoginScreen();

    }
}


document.addEventListener(
    "DOMContentLoaded",
    initializeSession
);


/* =====================================================
   NAVIGATION
===================================================== */

function showPage(pageId, button) {

    const targetPage = document.getElementById(pageId);

    if (!targetPage) {
        console.warn(`Page "${pageId}" was not found.`);
        return;
    }

    document.querySelectorAll(".page").forEach(page => {
        page.classList.remove("active");
    });

    document.querySelectorAll(".nav-btn").forEach(btn => {
        btn.classList.remove("active");
    });

    targetPage.classList.add("active");

    if (button) button.classList.add("active");

    const appShell = document.getElementById("appShell");
    if (appShell) appShell.classList.remove("mobile-nav-open");

    if (pageId === "dashboard") {
        loadWelfareCases();
    }

    if (pageId === "commanderOverview") {
        loadCommanderOverview();
    }
}


/* =====================================================
   COMMANDER OVERVIEW
===================================================== */

async function loadCommanderOverview() {

    const loading = document.getElementById("commanderLoading");
    const content = document.getElementById("commanderContent");

    if (loading) {
        loading.style.display = "block";
        loading.textContent = "Loading commander overview...";
    }

    if (content) content.style.display = "none";

    try {

        const response = await authFetch(
            `${API_URL}/commander/overview`
        );

        if (!response.ok) {

            let detail = "Unable to load commander overview.";

            try {
                const errorData = await response.json();
                if (errorData.detail) detail = errorData.detail;
            } catch (error) {
                // Keep default message.
            }

            throw new Error(detail);
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error("Commander overview could not be loaded.");
        }

        const scope = data.scope || {};
        const riskDistribution = data.risk_distribution || {};
        const operational = data.operational_summary || {};
        const welfare = data.welfare_summary || {};

        const scopeElement = document.getElementById("commanderScope");
        if (scopeElement) {
            scopeElement.textContent = scope.unit || "All authorized units";
        }

        document.getElementById("commanderPersonnelCount").textContent =
            scope.personnel_count ?? 0;

        document.getElementById("commanderActiveCases").textContent =
            welfare.active_welfare_cases ?? 0;

        document.getElementById("commanderFollowups").textContent =
            welfare.follow_up_scheduled ?? 0;

        document.getElementById("commanderLow").textContent =
            riskDistribution.Low ?? 0;

        document.getElementById("commanderModerate").textContent =
            riskDistribution.Moderate ?? 0;

        document.getElementById("commanderHigh").textContent =
            riskDistribution.High ?? 0;

        document.getElementById("avgDutyHours").textContent =
            formatOverviewNumber(operational.average_duty_hours_per_week);

        document.getElementById("avgDeploymentDays").textContent =
            formatOverviewNumber(operational.average_deployment_days);

        document.getElementById("avgLeaveDays").textContent =
            formatOverviewNumber(operational.average_days_since_last_leave);

        document.getElementById("avgNightDuties").textContent =
            formatOverviewNumber(operational.average_night_duties);

        document.getElementById("avgConsecutiveDays").textContent =
            formatOverviewNumber(operational.average_consecutive_duty_days);

        document.getElementById("avgFamilySeparation").textContent =
            formatOverviewNumber(operational.average_family_separation_days);

        document.getElementById("overviewActiveCases").textContent =
            welfare.active_welfare_cases ?? 0;

        document.getElementById("overviewFollowups").textContent =
            welfare.follow_up_scheduled ?? 0;

        document.getElementById("overviewImproving").textContent =
            welfare.improving ?? 0;

        if (loading) loading.style.display = "none";
        if (content) content.style.display = "block";

        console.log("Commander Overview:", data);

    } catch (error) {

        console.error(error);

        if (loading) {
            loading.style.display = "block";
            loading.innerHTML = `
                <div class="empty">
                    ⚠️ ${error.message || "Unable to load commander overview."}
                </div>
            `;
        }

        if (content) content.style.display = "none";
    }
}


function formatOverviewNumber(value) {

    if (value === null || value === undefined || Number.isNaN(Number(value))) {
        return "—";
    }

    const number = Number(value);

    return Number.isInteger(number)
        ? String(number)
        : number.toFixed(1);
}


/* =====================================================
   GET NUMBER
===================================================== */

function getNumber(id) {

    return Number(
        document.getElementById(id).value
    );

}


/* =====================================================
   ASSESS RISK
===================================================== */

async function assessRisk() {

    const user = getCurrentUser();

    if (!user) {
        showError("Authentication required. Please sign in again.");
        return;
    }

    const wellnessFields = [
        "phq9",
        "gad7",
        "sleep",
        "heart_rate",
        "hrv"
    ];

    const isPersonnel = user.role === "personnel";

    /*
        Personnel:
        - submits only voluntary wellness information
        - does NOT create or edit operational/HR data

        Authorized operational roles:
        - may enter prototype operational data
        - this simulates authorized HR/operational data ingestion
    */

    const requiredFields = isPersonnel
        ? wellnessFields
        : [
            ...wellnessFields,
            "days_since_leave",
            "deployment_days",
            "duty_hours",
            "night_duties",
            "consecutive_duty_days",
            "recent_transfer_count",
            "training_days",
            "family_separation_days"
        ];

    /* CHECK INPUTS */

    for (const field of requiredFields) {

        const element =
            document.getElementById(field);

        if (!element || element.value === "") {

            showError(
                isPersonnel
                    ? "Please complete all wellness fields."
                    : "Please fill in all wellness and operational fields."
            );

            return;
        }

    }

    const personnelDbId =
        isPersonnel
            ? user.personnel_id
            : PERSONNEL_DB_ID;

    if (!personnelDbId) {

        showError(
            "This account is not linked to a personnel record."
        );

        return;
    }

    try {

        /*
            =================================================
            PERSONNEL OPERATIONAL DATA
            =================================================

            Personnel users do not submit operational data.
            We verify that authorized operational data already
            exists for their linked personnel record.
        */

        if (isPersonnel) {

            const operationalResponse =
                await authFetch(
                    `${API_URL}/operational-data/${personnelDbId}`
                );

            if (!operationalResponse.ok) {

                if (
                    operationalResponse.status === 404
                ) {
                    throw new Error(
                        "Operational data is not yet available for your personnel record. Please contact the authorized welfare or HR administrator."
                    );
                }

                throw new Error(
                    "Authorized operational data could not be retrieved."
                );
            }

        }

        /*
            =================================================
            AUTHORIZED OPERATIONAL DATA
            =================================================

            Only authorized non-personnel roles use the
            prototype operational-data entry workflow.
        */

        if (!isPersonnel) {

            const operationalData = {

                personnel_id: personnelDbId,

                days_since_last_leave:
                    getNumber("days_since_leave"),

                deployment_days:
                    getNumber("deployment_days"),

                duty_hours_per_week:
                    getNumber("duty_hours"),

                night_duties:
                    getNumber("night_duties"),

                consecutive_duty_days:
                    getNumber("consecutive_duty_days"),

                recent_transfer_count:
                    getNumber("recent_transfer_count"),

                training_days:
                    getNumber("training_days"),

                family_separation_days:
                    getNumber("family_separation_days")

            };

            const operationalResponse =
                await authFetch(
                    `${API_URL}/operational-data`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body:
                            JSON.stringify(
                                operationalData
                            )
                    }
                );

            if (!operationalResponse.ok) {

                throw new Error(
                    "Operational data could not be saved."
                );

            }

        }

        /*
            =================================================
            WELLNESS DATA
            =================================================
        */

        const wellnessData = {

            personnel_id: personnelDbId,

            phq9_score:
                getNumber("phq9"),

            gad7_score:
                getNumber("gad7"),

            sleep_hours:
                getNumber("sleep"),

            heart_rate:
                getNumber("heart_rate"),

            hrv:
                getNumber("hrv")

        };

        /*
            =================================================
            CALL WELLNESS API
            =================================================
        */

        const wellnessResponse =
            await authFetch(
                `${API_URL}/wellness`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            wellnessData
                        )
                }
            );

        if (!wellnessResponse.ok) {

            let detail =
                "Wellness assessment failed.";

            try {

                const errorData =
                    await wellnessResponse.json();

                if (errorData.detail) {
                    detail = errorData.detail;
                }

            }
            catch (error) {
                // Keep the default message.
            }

            throw new Error(detail);

        }

        const result =
            await wellnessResponse.json();

        /*
            =================================================
            RESULT VALUES
            =================================================
        */

        const risk =
            result.risk_level || "Unknown";

        const trend =
            result.risk_trend || "Initial";

        const indicators =
            result.contributing_indicators ||
            "No major indicators recorded.";

        const recommendation =
            result.welfare_recommendation ||
            "Routine wellness monitoring recommended.";

        /*
            =================================================
            SHOW RESULT
            =================================================
        */

        showAssessmentResult(
            risk,
            trend,
            indicators,
            recommendation,
            result.previous_risk_level || null,
            result.risk_change || null,
            result.reassessment === true
        );

        console.log(
            "Wellness Result:",
            result
        );

    }

    catch (error) {

        console.error(error);

        showError(
            error.message ||
            "Unable to complete the wellness assessment."
        );

    }

}


/* =====================================================
   SHOW ASSESSMENT RESULT
===================================================== */

function showAssessmentResult(
    risk,
    trend,
    indicators,
    recommendation,
    previousRisk,
    riskChange,
    isReassessment
) {


    const result =
        document.getElementById("result");


    let className = "moderate";

    let icon = "🟡";


    if (risk === "Low") {

        className = "low";
        icon = "🟢";

    }

    else if (risk === "Moderate") {

        className = "moderate";
        icon = "🟡";

    }

    else if (risk === "High") {

        className = "high";
        icon = "🔴";

    }


    /* INDICATORS */

    const indicatorArray =
        indicators
            .split(",")
            .map(item => item.trim())
            .filter(item => item.length > 0);


    let indicatorHTML = "";


    indicatorArray.forEach(indicator => {

        indicatorHTML += `
            <li>• ${indicator}</li>
        `;

    });


    if (indicatorHTML === "") {

        indicatorHTML =
            "<li>• No major indicators recorded.</li>";

    }


    result.className = className;


    result.innerHTML = `

        <div class="result-header">

            <div class="result-icon">
                ${icon}
            </div>

            <div class="result-title">
                ${risk} Risk
            </div>

        </div>


        <div class="result-summary">


            <div class="result-box">

                <div class="result-box-label">
                    Current Risk
                </div>

                <div class="result-box-value">
                    ${risk}
                </div>

            </div>


            <div class="result-box">

                <div class="result-box-label">
                    Risk Trend
                </div>

                <div class="result-box-value">
                    ${trend}
                </div>

            </div>


        </div>


        ${isReassessment ? `

        <div class="result-section">

            <h3>
                Reassessment Summary
            </h3>

            <div class="result-summary">

                <div class="result-box">

                    <div class="result-box-label">
                        Previous Risk
                    </div>

                    <div class="result-box-value">
                        ${previousRisk || "Not available"}
                    </div>

                </div>

                <div class="result-box">

                    <div class="result-box-label">
                        Current Risk
                    </div>

                    <div class="result-box-value">
                        ${risk}
                    </div>

                </div>

                <div class="result-box">

                    <div class="result-box-label">
                        Change
                    </div>

                    <div class="result-box-value">
                        ${riskChange || "No change"}
                    </div>

                </div>

            </div>

            <div class="recommendation-result" style="margin-top:12px;">
                This reassessment is compared with the previous
                ML-generated risk assessment. Welfare case status
                remains under authorized human control.
            </div>

        </div>

        ` : ""}


        <div class="result-section">

            <h3>
                Contributing Indicators
            </h3>

            <ul class="indicator-list-result">

                ${indicatorHTML}

            </ul>

        </div>


        <div class="result-section">

            <h3>
                Welfare Recommendation
            </h3>

            <div class="recommendation-result">

                ${recommendation}

            </div>

        </div>

    `;


    result.style.display = "block";


    result.scrollIntoView({
        behavior: "smooth",
        block: "nearest"
    });

}


/* =====================================================
   ERROR RESULT
===================================================== */

function showError(message) {


    const result =
        document.getElementById("result");


    result.className = "error";


    result.innerHTML = `

        <div class="result-header">

            <div class="result-icon">
                ⚠️
            </div>

            <div class="result-title">
                Assessment Error
            </div>

        </div>

        <div class="recommendation-result">

            ${message}

        </div>

    `;


    result.style.display = "block";

}


/* =====================================================
   LOAD WELFARE CASES
===================================================== */

async function loadWelfareCases() {


    const container =
        document.getElementById(
            "casesContainer"
        );


    container.innerHTML =
        `
        <div class="loading">
            Loading welfare cases...
        </div>
        `;


    try {


        const response =
            await authFetch(
                `${API_URL}/welfare-cases`
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load welfare cases."
            );

        }


        const data =
            await response.json();


        const cases =
            data.welfare_cases || [];


        updateStatistics(cases);

        displayWelfareCases(cases);


    }

    catch (error) {


        container.innerHTML =

            `
            <div class="empty">
                ⚠️ Could not load welfare cases.
            </div>
            `;


        console.error(error);

    }

}


/* =====================================================
   DASHBOARD STATISTICS
===================================================== */

function updateStatistics(cases) {


    const total =
        cases.length;


    const attention =
        cases.filter(
            item =>
                item.status ===
                "Attention Required"
        ).length;

    
    const now = new Date();

const followup =
    cases.filter(item => {
        if (!item.follow_up_date) {
            return false;
        }

        const followUpDate =
            new Date(item.follow_up_date);

        return followUpDate > now;
    }).length;
                

    const improving =
        cases.filter(
            item =>
                item.status ===
                "Improving"
        ).length;


    document.getElementById(
        "totalCases"
    ).textContent = total;


    document.getElementById(
        "attentionCases"
    ).textContent = attention;


    document.getElementById(
        "followupCases"
    ).textContent = followup;


    document.getElementById(
        "improvingCases"
    ).textContent = improving;

}


/* =====================================================
   DISPLAY WELFARE CASES
===================================================== */

function displayWelfareCases(cases) {


    const container =
        document.getElementById(
            "casesContainer"
        );


    if (!cases || cases.length === 0) {

        container.innerHTML =

            `
            <div class="empty">
                No welfare cases found.
            </div>
            `;

        return;

    }


    let html = `

        <table>

            <thead>

                <tr>

                    <th>Personnel</th>
                    <th>Risk</th>
                    <th>Trend</th>
                    <th>Status</th>
                    <th>Officer</th>
                    <th>Action</th>

                </tr>

            </thead>

            <tbody>

    `;


    cases.forEach(item => {


        const risk =
            item.risk?.risk_level ||
            "Unknown";


        const trend =
            item.risk?.risk_trend ||
            "Unknown";


        const personnel =
            item.personnel ||
            {};


        html += `

            <tr>

                <td>

                    <strong>
                        ${personnel.name || "Unknown"}
                    </strong>

                    <br>

                    <small>
                        ${personnel.personnel_id || "N/A"}
                    </small>

                </td>


                <td>

                    <span
                        class="badge ${getRiskClass(risk)}"
                    >
                        ${risk}
                    </span>

                </td>


                <td>

                    <span
                        class="badge ${getTrendClass(trend)}"
                    >
                        ${trend}
                    </span>

                </td>


                <td>

                    <span
                        class="badge ${getStatusClass(item.status)}"
                    >
                        ${item.status || "Unknown"}
                    </span>

                </td>


                <td>

                    ${item.assigned_officer || "Not assigned"}

                </td>


                <td>

                    <button
                        class="view-btn"
                        onclick="viewCase(${item.welfare_case_id})"
                    >
                        View
                    </button>

                </td>

            </tr>

        `;

    });


    html += `

            </tbody>

        </table>

    `;


    container.innerHTML =
        html;

}


/* =====================================================
   BADGES
===================================================== */

function getRiskClass(risk) {

    if (risk === "Low")
        return "badge-low";

    if (risk === "Moderate")
        return "badge-moderate";

    if (risk === "High")
        return "badge-high";

    return "badge-stable";

}


function getTrendClass(trend) {

    if (trend === "Worsening") {
        trend = "Worsening";
    }

    if (trend === "Improving")
        return "badge-improving";

    if (trend === "Worsening")
        return "badge-increasing";

    return "badge-stable";

}


function getStatusClass(status) {

    if (status === "Attention Required")
        return "badge-attention";

    if (status === "Intervention Initiated")
        return "badge-intervention";

    if (status === "Follow-up Scheduled")
        return "badge-moderate";

    if (status === "Improving")
        return "badge-improving";

    return "badge-stable";

}


/* =====================================================
   VIEW + MANAGE WELFARE CASE
===================================================== */

let activeWelfareCase = null;
let activeFollowUps = [];

async function viewCase(caseId) {
    const details = document.getElementById('caseDetails');
    const content = document.getElementById('caseDetailsContent');
    details.style.display = 'block';
    content.innerHTML = '<div class="loading">Loading case details...</div>';

    try {
        const casesResponse = await authFetch(`${API_URL}/welfare-cases`);
        if (!casesResponse.ok) throw new Error('Unable to load welfare cases.');

        const casesData = await casesResponse.json();
        const caseData = (casesData.welfare_cases || []).find(
            item => item.welfare_case_id === caseId
        );
        if (!caseData) throw new Error('Case not found.');

        const followupResponse = await authFetch(`${API_URL}/follow-ups/${caseId}`);
        let followupData = { success: false, total_follow_ups: 0, follow_ups: [] };
        if (followupResponse.ok) followupData = await followupResponse.json();

        activeWelfareCase = caseData;
        activeFollowUps = followupData.follow_ups || [];
        renderWelfareCaseDetails(caseData, activeFollowUps);
        details.scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        content.innerHTML = '<div class="empty">⚠️ Could not load case details.</div>';
        console.error(error);
    }
}

function renderWelfareCaseDetails(caseData, followUps) {
    const content = document.getElementById('caseDetailsContent');
    const personnel = caseData.personnel || {};
    const risk = caseData.risk?.risk_level || 'Unknown';
    const trend = caseData.risk?.risk_trend || 'Unknown';
    const indicators = caseData.risk?.contributing_indicators || 'No major indicators recorded.';
    const reassessmentHistory = caseData.reassessment_history || [];

    const indicatorArray = indicators.split(',').map(item => item.trim()).filter(Boolean);
    const indicatorHTML = indicatorArray.map(indicator => `<li>${indicator}</li>`).join('');

    let reassessmentHTML = '<p>No reassessment history recorded yet.</p>';
    if (reassessmentHistory.length > 0) {
        reassessmentHTML = `
            <div class="detail-grid">
                ${reassessmentHistory.map((item, index) => {
                    const previous = reassessmentHistory[index + 1]?.risk_level || null;
                    let change = 'Initial assessment';
                    if (previous) {
                        const score = { Low: 1, Moderate: 2, High: 3 };
                        if (score[item.risk_level] < score[previous]) change = 'Improved';
                        else if (score[item.risk_level] > score[previous]) change = 'Worsened';
                        else change = 'No change';
                    }
                    return `
                        <div class="detail-box">
                            <strong>Assessment ${reassessmentHistory.length - index}</strong>
                            <div style="margin-top:8px;"><b>Risk:</b> <span class="badge ${getRiskClass(item.risk_level)}">${item.risk_level || 'Unknown'}</span></div>
                            <div><b>Trend:</b> ${item.risk_trend || 'Not recorded'}</div>
                            <div><b>Change:</b> ${change}</div>
                            <div style="margin-top:6px;color:#64748b;font-size:12px;">Assessed: ${formatDate(item.created_at)}</div>
                        </div>
                    `;
                }).join('')}
            </div>
            <p style="margin-top:10px;color:#64748b;font-size:12px;">Reassessment history compares successive ML-generated risk assessments. Welfare case actions remain under authorized human control.</p>
        `;
    }

    let followupHTML = '<p>No follow-up records found.</p>';
    if (followUps.length > 0) {
        followupHTML = `
            <div class="detail-grid">
                ${followUps.map((item, index) => `
                    <div class="detail-box">
                        <strong>Follow-up ${followUps.length - index}</strong>
                        <div style="margin-top:8px;"><b>Risk:</b> ${item.risk_level || 'Not recorded'}</div>
                        <div><b>Trend:</b> ${item.risk_trend || 'Not recorded'}</div>
                        <div><b>Outcome:</b> ${item.outcome || 'Not recorded'}</div>
                        <div><b>Notes:</b> ${item.notes || 'No notes recorded.'}</div>
                        <div><b>Next Follow-up:</b> ${formatDate(item.next_follow_up_date)}</div>
                        <div style="margin-top:6px;color:#64748b;font-size:12px;">Recorded: ${formatDate(item.created_at)}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    content.innerHTML = `
        <div class="detail-grid">
            <div class="detail-box"><strong>Personnel</strong>${personnel.name || 'Unknown'}</div>
            <div class="detail-box"><strong>Personnel ID</strong>${personnel.personnel_id || 'N/A'}</div>
            <div class="detail-box"><strong>Current Risk</strong><span class="badge ${getRiskClass(risk)}">${risk}</span></div>
            <div class="detail-box"><strong>Risk Trend</strong><span class="badge ${getTrendClass(trend)}">${trend}</span></div>
            <div class="detail-box"><strong>Case Status</strong>${caseData.status || 'Unknown'}</div>
            <div class="detail-box"><strong>Assigned Officer</strong>${caseData.assigned_officer || 'Not assigned'}</div>
        </div>

        <div class="section">
            <h3>Contributing Indicators</h3>
            <ul class="indicator-list">${indicatorHTML}</ul>
        </div>

        <div class="recommendation">
            <strong>Welfare Recommendation</strong>
            <p style="margin-top:8px;">${getRecommendation(risk, trend)}</p>
        </div>

        <div class="section">
            <h3>Reassessment History</h3>
            <p style="margin-top:6px;color:#64748b;font-size:13px;">Track how the ML-generated risk assessment changes over time after welfare follow-up and reassessment.</p>
            ${reassessmentHTML}
        </div>

        <div class="section">
            <h3>Manage Welfare Case</h3>
            <p style="margin-top:6px;color:#64748b;font-size:13px;">
                Update the welfare-support workflow. These actions are for authorized welfare personnel and should not be used for disciplinary decisions.
            </p>

            <div class="detail-grid">
                <div class="detail-box">
                    <label for="caseStatus">Case Status</label>
                    <select id="caseStatus" class="form-control">
                        <option value="Attention Required">Attention Required</option>
                        <option value="Intervention Initiated">Intervention Initiated</option>
                        <option value="Follow-up Scheduled">Follow-up Scheduled</option>
                        <option value="Improving">Improving</option>
                        <option value="Routine Monitoring">Routine Monitoring</option>
                    </select>
                </div>
                <div class="detail-box">
                    <label for="interventionType">Intervention Type</label>
                    <input id="interventionType" class="form-control" type="text" placeholder="e.g. Welfare check-in" value="${caseData.intervention_type || ''}">
                </div>
                <div class="detail-box">
                    <label for="assignedOfficer">Assigned Officer</label>
                    <input id="assignedOfficer" class="form-control" type="text" placeholder="Officer name / ID" value="${caseData.assigned_officer || ''}">
                </div>
                <div class="detail-box">
                    <label for="caseFollowUpDate">Follow-up Date</label>
                    <input id="caseFollowUpDate" class="form-control" type="datetime-local" value="${toDateTimeLocal(caseData.follow_up_date)}">
                </div>
            </div>

            <div style="margin-top:15px;">
                <label for="caseNotes">Case Notes</label>
                <textarea id="caseNotes" class="form-control" rows="4" placeholder="Record welfare-related notes, support actions or follow-up context...">${caseData.notes || ''}</textarea>
            </div>

            <div style="margin-top:15px;">
                <button class="view-btn" onclick="saveWelfareCaseUpdate(${caseData.welfare_case_id})">Save Case Update</button>
            </div>
            <div id="caseUpdateMessage" style="margin-top:10px;"></div>
        </div>

        <div class="section">
            <h3>Record Follow-up</h3>
            <p style="margin-top:6px;color:#64748b;font-size:13px;">
                Record the outcome of the welfare follow-up and schedule the next review when needed.
            </p>

            <div class="detail-grid">
                <div class="detail-box">
                    <label for="followupRisk">Current Risk</label>
                    <select id="followupRisk" class="form-control">
                        <option value="Low">Low</option>
                        <option value="Moderate">Moderate</option>
                        <option value="High">High</option>
                    </select>
                </div>
                <div class="detail-box">
                    <label for="followupTrend">Risk Trend</label>
                    <select id="followupTrend" class="form-control">
                        <option value="Improving">Improving</option>
                        <option value="Stable">Stable</option>
                        <option value="Worsening">Worsening</option>
                    </select>
                </div>
                <div class="detail-box">
                    <label for="followupOutcome">Outcome</label>
                    <select id="followupOutcome" class="form-control">
                        <option value="Support initiated">Support initiated</option>
                        <option value="Follow-up completed">Follow-up completed</option>
                        <option value="Improving">Improving</option>
                        <option value="Stable">Stable</option>
                        <option value="Further support required">Further support required</option>
                    </select>
                </div>
                <div class="detail-box">
                    <label for="nextFollowUpDate">Next Follow-up Date</label>
                    <input id="nextFollowUpDate" class="form-control" type="datetime-local">
                </div>
            </div>

            <div style="margin-top:15px;">
                <label for="followupNotes">Follow-up Notes</label>
                <textarea id="followupNotes" class="form-control" rows="4" placeholder="Record the follow-up outcome and relevant welfare support..."></textarea>
            </div>

            <div style="margin-top:15px;">
                <button class="view-btn" onclick="recordWelfareFollowUp(${caseData.welfare_case_id})">Record Follow-up</button>
            </div>
            <div id="followupMessage" style="margin-top:10px;"></div>
        </div>

        <div class="section">
            <h3>Follow-up History</h3>
            ${followupHTML}
        </div>
    `;

    const statusElement = document.getElementById('caseStatus');
    if (statusElement) statusElement.value = caseData.status || 'Attention Required';

    const followupRiskElement = document.getElementById('followupRisk');
    if (followupRiskElement) followupRiskElement.value = risk;

    const followupTrendElement = document.getElementById('followupTrend');
    if (followupTrendElement) {
        followupTrendElement.value = ['Improving', 'Stable', 'Worsening'].includes(trend) ? trend : 'Stable';
    }
}

async function saveWelfareCaseUpdate(caseId) {
    const message = document.getElementById('caseUpdateMessage');
    const payload = {
        status: document.getElementById('caseStatus').value,
        intervention_type: document.getElementById('interventionType').value.trim() || null,
        assigned_officer: document.getElementById('assignedOfficer').value.trim() || null,
        notes: document.getElementById('caseNotes').value.trim() || null,
        follow_up_date: document.getElementById('caseFollowUpDate').value
            ? new Date(document.getElementById('caseFollowUpDate').value).toISOString()
            : null
    };

    message.innerHTML = '<span style="color:#64748b;">Saving case update...</span>';

    try {
        const response = await authFetch(`${API_URL}/welfare-cases/${caseId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Unable to update welfare case.');

        message.innerHTML = '<span style="color:#15803d;">✓ Welfare case updated successfully.</span>';
        await loadWelfareCases();
        await viewCase(caseId);
    } catch (error) {
        message.innerHTML = `<span style="color:#dc2626;">⚠️ ${error.message}</span>`;
        console.error(error);
    }
}

async function recordWelfareFollowUp(caseId) {
    const message = document.getElementById('followupMessage');
    const nextDateValue = document.getElementById('nextFollowUpDate').value;

    const payload = {
        welfare_case_id: caseId,
        risk_level: document.getElementById('followupRisk').value,
        risk_trend: document.getElementById('followupTrend').value,
        outcome: document.getElementById('followupOutcome').value,
        notes: document.getElementById('followupNotes').value.trim() || null,
        next_follow_up_date: nextDateValue ? new Date(nextDateValue).toISOString() : null
    };

    message.innerHTML = '<span style="color:#64748b;">Recording follow-up...</span>';

    try {
        const response = await authFetch(`${API_URL}/follow-ups`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Unable to record follow-up.');

        message.innerHTML = '<span style="color:#15803d;">✓ Follow-up recorded successfully.</span>';
        await loadWelfareCases();
        await viewCase(caseId);
    } catch (error) {
        message.innerHTML = `<span style="color:#dc2626;">⚠️ ${error.message}</span>`;
        console.error(error);
    }
}

function toDateTimeLocal(dateValue) {
    if (!dateValue) return '';
    const date = new Date(dateValue);
    if (Number.isNaN(date.getTime())) return '';
    const offset = date.getTimezoneOffset();
    const localDate = new Date(date.getTime() - offset * 60 * 1000);
    return localDate.toISOString().slice(0, 16);
}

/* =====================================================
   WELFARE RECOMMENDATION
===================================================== */

function getRecommendation(
    risk,
    trend
) {


    if (risk === "High") {

        return (
            "Confidential welfare review recommended. " +
            "Prioritize human review and consider workload, " +
            "recovery, leave and available support resources."
        );

    }


    if (
        risk === "Moderate" &&
        (trend === "Worsening" || trend === "Worsening")
    ) {

        return (
            "Confidential welfare check-in recommended. " +
            "Review workload, recovery, sleep and leave patterns."
        );

    }


    if (risk === "Moderate") {

        return (
            "Welfare follow-up recommended. " +
            "Continue monitoring wellbeing and relevant operational factors."
        );

    }


    if (
        risk === "Low" &&
        trend === "Improving"
    ) {

        return (
            "Wellbeing appears to be improving. " +
            "Continue routine monitoring and available wellness support."
        );

    }


    return (
        "Routine wellness monitoring recommended."
    );

}


/* =====================================================
   DATE FORMAT
===================================================== */

function formatDate(dateValue) {

    if (!dateValue) {

        return "Not scheduled";

    }


    const date =
        new Date(dateValue);


    return date.toLocaleString();

}


/* =====================================================
   ROLE-AWARE UI PRESENTATION
   UI ONLY — does not change API permissions or backend logic.
===================================================== */

function applyRolePresentation(user) {

    const appShell = document.getElementById("appShell");
    const role = user?.role || "";

    if (appShell) {
        appShell.dataset.role = role;
    }

    const roleTitle = document.getElementById("roleWelcomeTitle");
    const roleSubtitle = document.getElementById("roleWelcomeSubtitle");

    const copy = {
        personnel: {
            title: "Your wellbeing, securely supported",
            subtitle:
                "Complete a voluntary wellness check and review the support available to you."
        },
        welfare_officer: {
            title: "Welfare support command center",
            subtitle:
                "Review authorized welfare cases, follow-ups and reassessment trends."
        },
        commander: {
            title: "Unit welfare & readiness overview",
            subtitle:
                "Use aggregate indicators to support workload, recovery and welfare planning."
        },
        admin: {
            title: "SAATHI administration",
            subtitle:
                "Manage the platform while maintaining role-based access and welfare-first controls."
        }
    };

    const selected = copy[role] || copy.personnel;

    if (roleTitle) roleTitle.textContent = selected.title;
    if (roleSubtitle) roleSubtitle.textContent = selected.subtitle;

    const assessmentButton =
        document.getElementById("assessmentNavButton");

    const dashboardButton =
        document.getElementById("dashboardNavButton");

    const commanderButton =
        document.getElementById("commanderNavButton");

    /*
        Every role gets a deterministic landing page.
        This prevents a previous user's dashboard from leaking
        into the next user's session.
    */

    if (assessmentButton) {
        assessmentButton.style.display =
            role === "personnel" || role === "admin"
                ? "inline-flex"
                : "none";
    }

    if (dashboardButton) {
        dashboardButton.style.display =
            role === "welfare_officer" || role === "admin"
                ? "inline-flex"
                : "none";
    }

    if (commanderButton) {
        commanderButton.style.display =
            role === "commander" || role === "admin"
                ? "inline-flex"
                : "none";
    }

    if (role === "welfare_officer" && dashboardButton) {
        showPage("dashboard", dashboardButton);
        return;
    }

    if (role === "commander" && commanderButton) {
        showPage("commanderOverview", commanderButton);
        return;
    }

    if (assessmentButton) {
        showPage("assessment", assessmentButton);
    }
}


/* =====================================================
   LOGIN MICRO-INTERACTIONS
===================================================== */

document.addEventListener("DOMContentLoaded", () => {

    const usernameInput = document.getElementById("loginUsername");
    const passwordInput = document.getElementById("loginPassword");

    [usernameInput, passwordInput]
        .filter(Boolean)
        .forEach(input => {

            input.addEventListener("input", () => {
                const errorBox = document.getElementById("loginError");

                if (errorBox) {
                    errorBox.style.display = "none";
                    errorBox.textContent = "";
                }
            });

            input.addEventListener("keydown", event => {
                if (
                    event.key === "Enter" &&
                    usernameInput?.value.trim() &&
                    passwordInput?.value
                ) {
                    login();
                }
            });
        });
});
