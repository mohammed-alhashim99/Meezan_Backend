from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework import status

from .parsers.csv_parser import parse_csv


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

    uploaded = request.FILES['file']
    name = uploaded.name.lower()

    if name.endswith('.csv'):
        try:
            transactions = parse_csv(uploaded)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except Exception as e:
            return Response(
                {'error': f'Failed to parse CSV: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    elif name.endswith('.pdf'):
        # PDF parsing — Day 3
        return Response(
            {'error': 'PDF parsing coming soon'},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )

    else:
        return Response(
            {'error': 'Only CSV and PDF files are supported'},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({
        'file_name':        uploaded.name,
        'transaction_count': len(transactions),
        'transactions':     transactions,
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
    # Claude categorization — Day 6
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
    # Claude insights — Day 8
    return Response({'insights': []})
