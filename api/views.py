from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok', 'message': 'Meezan API is running'})


@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_file(request):
    if 'file' not in request.FILES:
        return Response(
            {'error': 'No file provided'},
            status=status.HTTP_400_BAD_REQUEST
        )

    uploaded_file = request.FILES['file']
    file_name = uploaded_file.name

    if not (file_name.endswith('.csv') or file_name.endswith('.pdf')):
        return Response(
            {'error': 'Only CSV and PDF files are supported'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Placeholder — parsing logic comes in Day 2-3
    return Response({
        'message': 'File received successfully',
        'file_name': file_name,
        'file_size': uploaded_file.size,
        'transactions': []
    })


@api_view(['POST'])
@parser_classes([JSONParser])
def categorize_transactions(request):
    transactions = request.data.get('transactions', [])
    if not transactions:
        return Response(
            {'error': 'No transactions provided'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Placeholder — Claude categorization comes in Day 6
    return Response({'transactions': transactions})


@api_view(['POST'])
@parser_classes([JSONParser])
def get_insights(request):
    transactions = request.data.get('transactions', [])
    if not transactions:
        return Response(
            {'error': 'No transactions provided'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Placeholder — Claude insights come in Day 8
    return Response({'insights': []})
