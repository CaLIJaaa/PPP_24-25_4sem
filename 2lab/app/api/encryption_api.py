from fastapi import APIRouter
from app.schemas.encryption_schemas import EncodeRequest, EncodeResponse, DecodeRequest, DecodeResponse
from app.services.encryption_service import encode_text, decode_text

router = APIRouter()

@router.post("/encode", response_model=EncodeResponse)
async def encode(request: EncodeRequest):
    encoded_data, key, huffman_codes, padding = encode_text(request.text, request.key)
    return EncodeResponse(
        encoded_data=encoded_data,
        key=key,
        huffman_codes=huffman_codes,
        padding=padding
    )

@router.post("/decode", response_model=DecodeResponse)
async def decode(request: DecodeRequest):
    decoded_text_result = decode_text(request.encoded_data, request.key, request.huffman_codes, request.padding)
    return DecodeResponse(decoded_text=decoded_text_result) 