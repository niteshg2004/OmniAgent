from __future__ import annotations
"""Concrete execution plan generation."""

import logging

from app.planner.intent import IntentResult, IntentType
from app.planner.planner import Planner
from app.schemas.agent import AgentRequest
from app.schemas.trace import PlanStep
from app.utils.file_utils import FileType, detect_file_type
from app.utils.text_utils import extract_youtube_urls

logger = logging.getLogger(__name__)

_EXTRACTOR_BY_TYPE: dict[FileType, str] = {
    FileType.PDF: "pdf_extractor",
    FileType.IMAGE: "image_ocr",
    FileType.AUDIO: "audio_transcriber",
    FileType.TEXT: "text_reader",
}


class OmniAgentPlanner(Planner):
    """Builds minimal tool chains from intent and uploaded files."""

    def create_plan(
        self, request: AgentRequest, intent: IntentResult
    ) -> list[PlanStep]:
        """Build the shortest valid tool chain for the given intent."""
        if intent.intent == IntentType.AMBIGUOUS:
            return []

        files = self._indexed_files(request)
        message = (request.message or "").strip()
        steps: list[PlanStep] = []
        step_num = 1

        if intent.intent == IntentType.YOUTUBE_SUMMARIZE:
            steps = self._plan_youtube_summarize(files, message, step_num)
        elif intent.intent == IntentType.TRANSCRIBE:
            steps = self._plan_transcribe(files, step_num)
        elif intent.intent == IntentType.EXTRACT_TEXT:
            steps = self._plan_extract(files, step_num)
        elif intent.intent == IntentType.SUMMARIZE:
            steps = self._plan_extract(files, step_num)
            if steps:
                step_num = steps[-1].step + 1
            steps.append(
                PlanStep(step=step_num, tool="summarizer", params={"text": "$prev"})
            )
        elif intent.intent == IntentType.SENTIMENT_ANALYSIS:
            steps = self._plan_extract(files, step_num)
            if steps:
                step_num = steps[-1].step + 1
            steps.append(
                PlanStep(
                    step=step_num,
                    tool="sentiment_analyzer",
                    params={"text": "$prev"},
                )
            )
        elif intent.intent == IntentType.CODE_ANALYSIS:
            steps = self._plan_extract(files, step_num)
            if steps:
                step_num = steps[-1].step + 1
            steps.append(
                PlanStep(step=step_num, tool="code_analyzer", params={"text": "$prev"})
            )
        elif intent.intent == IntentType.CUSTOM:
            steps = self._plan_extract(files, step_num)
            if steps:
                step_num = steps[-1].step + 1
            steps.append(
                PlanStep(step=step_num, tool="summarizer", params={"text": "$prev"})
            )
        else:
            steps = self._plan_extract(files, step_num)

        logger.info(
            "Plan created: intent=%s steps=%s",
            intent.intent.value,
            [s.tool for s in steps],
        )
        return steps

    def _indexed_files(self, request: AgentRequest) -> list[dict[str, str]]:
        """Return file metadata list with paths, names, and types."""
        indexed: list[dict[str, str]] = []
        for path, name in zip(request.file_paths, request.file_names):
            file_type = detect_file_type(name or path)
            indexed.append(
                {
                    "path": path,
                    "name": name,
                    "type": file_type.value,
                }
            )
        return indexed

    def _plan_extract(
        self, files: list[dict[str, str]], start_step: int
    ) -> list[PlanStep]:
        """Plan extraction steps for all uploaded files."""
        steps: list[PlanStep] = []
        step_num = start_step

        for index, file_info in enumerate(files):
            file_type = FileType(file_info["type"])
            if file_type == FileType.UNKNOWN:
                continue

            tool = _EXTRACTOR_BY_TYPE.get(file_type)
            if tool:
                steps.append(
                    PlanStep(
                        step=step_num,
                        tool=tool,
                        params={"file_path": f"$file:{index}"},
                    )
                )
                step_num += 1

        return steps

    def _plan_transcribe(
        self, files: list[dict[str, str]], start_step: int
    ) -> list[PlanStep]:
        """Plan audio transcription steps."""
        steps: list[PlanStep] = []
        step_num = start_step
        for index, file_info in enumerate(files):
            if file_info["type"] == FileType.AUDIO.value:
                steps.append(
                    PlanStep(
                        step=step_num,
                        tool="audio_transcriber",
                        params={"file_path": f"$file:{index}"},
                    )
                )
                step_num += 1
        return steps

    def _plan_youtube_summarize(
        self,
        files: list[dict[str, str]],
        message: str,
        start_step: int,
    ) -> list[PlanStep]:
        """Plan PDF→URL→transcript→summary or direct URL→transcript→summary."""
        steps: list[PlanStep] = []
        step_num = start_step
        has_url_in_message = bool(extract_youtube_urls(message))

        if not has_url_in_message:
            pdf_index = next(
                (i for i, f in enumerate(files) if f["type"] == FileType.PDF.value),
                None,
            )
            if pdf_index is not None:
                steps.append(
                    PlanStep(
                        step=step_num,
                        tool="pdf_extractor",
                        params={"file_path": f"$file:{pdf_index}"},
                    )
                )
                step_num += 1
                steps.append(
                    PlanStep(
                        step=step_num,
                        tool="youtube_transcript",
                        params={"text": "$prev"},
                    )
                )
                step_num += 1
            else:
                steps.append(
                    PlanStep(
                        step=step_num,
                        tool="youtube_transcript",
                        params={"text": message},
                    )
                )
                step_num += 1
        else:
            steps.append(
                PlanStep(
                    step=step_num,
                    tool="youtube_transcript",
                    params={"url": message},
                )
            )
            step_num += 1

        steps.append(
            PlanStep(step=step_num, tool="summarizer", params={"text": "$prev"})
        )
        return steps
