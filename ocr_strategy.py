from abc import ABC, abstractmethod


class OCRStrategy(ABC):

    @abstractmethod
    def handle_ocr_result(
        self,
        engine,
        region_key,
        request_id,
        normalized_text,
        source_text,
    ):
        pass


class RealtimeStrategy:

    def handle_ocr_result(
        self,
        engine,
        region_key,
        request_id,
        normalized_text,
        source_text,
    ):
        engine._queue_translation(
            normalized_text,
            source_text,
            region_key,
            request_id,
        )


class ReadingStrategy:

    def handle_ocr_result(
        self,
        engine,
        region_key,
        request_id,
        normalized_text,
        source_text,
    ):
        engine._schedule_reading_translation(
            normalized_text,
            source_text,
            region_key,
            request_id,
        )



class ScrollingStrategy:

    def handle_ocr_result(
        self,
        engine,
        region_key,
        request_id,
        normalized_text,
        source_text,
    ):
        engine._schedule_scrolling_translation(
            region_key,
            request_id,
            normalized_text,
            source_text,
        )




