import logging
import time

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from app.models.schemas import ResumeAnalysisResponse, ResumeOptimizationResponse
from app.services.file_reader import read_uploaded_file
from app.services.analyzer import analyze_resume_match
from app.services.optimizer import optimize_resume


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger("resume_analyzer_backend")


app = FastAPI(
    title="Resume Analyzer AI Backend",
    description="Backend API for matching and optimizing resume PDF with job requirements using OpenAI.",
    version="1.1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    logger.info(f"Incoming request: {request.method} {request.url.path}")

    response = await call_next(request)

    process_time = round(time.time() - start_time, 4)

    logger.info(
        f"Completed request: {request.method} {request.url.path} "
        f"Status={response.status_code} Time={process_time}s"
    )

    return response


@app.on_event("startup")
async def show_registered_routes():
    logger.info("Application startup complete.")
    logger.info("Registered API routes:")

    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)

        if methods and path:
            logger.info(f"{methods} {path}")


@app.get("/debug/routes")
def debug_routes():
    routes = []

    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        name = getattr(route, "name", None)

        if methods and path:
            routes.append(
                {
                    "path": path,
                    "methods": list(methods),
                    "name": name
                }
            )

    return {
        "message": "Registered routes",
        "routes": routes
    }


@app.get("/health")
def health_check():
    logger.info("Health check endpoint called.")

    return {
        "status": "running",
        "message": "Resume Analyzer Backend is working"
    }


@app.post("/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    job_file: UploadFile = File(...),
    resume_file: UploadFile = File(...)
):
    logger.info("Analyze resume endpoint called.")

    try:
        logger.info(f"Job file received: {job_file.filename}")
        logger.info(f"Resume file received: {resume_file.filename}")

        if not resume_file.filename.lower().endswith(".pdf"):
            logger.warning("Invalid resume file type.")
            raise HTTPException(
                status_code=400,
                detail="Resume must be uploaded as a PDF file."
            )

        job_requirement_text = await read_uploaded_file(job_file)
        resume_text = await read_uploaded_file(resume_file)

        logger.info(f"Job requirement text length: {len(job_requirement_text)}")
        logger.info(f"Resume text length: {len(resume_text)}")

        if not job_requirement_text:
            logger.warning("Job requirement file is empty or unreadable.")
            raise HTTPException(
                status_code=400,
                detail="Job requirement file is empty or unreadable."
            )

        if not resume_text:
            logger.warning("Resume file is empty or unreadable.")
            raise HTTPException(
                status_code=400,
                detail="Resume file is empty or unreadable."
            )

        result = analyze_resume_match(
            job_requirement_text=job_requirement_text,
            resume_text=resume_text
        )

        logger.info("Analyze resume completed successfully.")

        return result

    except HTTPException:
        raise

    except ValueError as error:
        logger.exception("ValueError occurred while analyzing resume.")
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        logger.exception("Unexpected error occurred while analyzing resume.")
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while analyzing resume: {str(error)}"
        )


@app.post("/optimize", response_model=ResumeOptimizationResponse)
async def optimize_uploaded_resume(
    job_file: UploadFile = File(...),
    resume_file: UploadFile = File(...)
):
    logger.info("Optimize resume endpoint called.")

    try:
        logger.info(f"Job file received: {job_file.filename}")
        logger.info(f"Resume file received: {resume_file.filename}")

        if not resume_file.filename.lower().endswith(".pdf"):
            logger.warning("Invalid resume file type.")
            raise HTTPException(
                status_code=400,
                detail="Resume must be uploaded as a PDF file."
            )

        job_requirement_text = await read_uploaded_file(job_file)
        resume_text = await read_uploaded_file(resume_file)

        logger.info(f"Job requirement text length: {len(job_requirement_text)}")
        logger.info(f"Resume text length: {len(resume_text)}")

        if not job_requirement_text:
            logger.warning("Job requirement file is empty or unreadable.")
            raise HTTPException(
                status_code=400,
                detail="Job requirement file is empty or unreadable."
            )

        if not resume_text:
            logger.warning("Resume file is empty or unreadable.")
            raise HTTPException(
                status_code=400,
                detail="Resume file is empty or unreadable."
            )

        logger.info("Calling optimize_resume service.")

        result = optimize_resume(
            job_requirement_text=job_requirement_text,
            resume_text=resume_text
        )

        logger.info("Optimize resume completed successfully.")

        return result

    except HTTPException:
        raise

    except ValueError as error:
        logger.exception("ValueError occurred while optimizing resume.")
        raise HTTPException(status_code=400, detail=str(error))

    except Exception as error:
        logger.exception("Unexpected error occurred while optimizing resume.")
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while optimizing resume: {str(error)}"
        )