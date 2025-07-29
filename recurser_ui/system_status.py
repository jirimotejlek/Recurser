import time
from typing import Dict, List, Optional

import requests
import streamlit as st


def check_service_health(service_name: str, url: str, timeout: int = 5) -> Dict:
    """Check the health of a specific service"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            return {
                "status": "🟢 Online",
                "healthy": True,
                "response_time": response.elapsed.total_seconds(),
                "details": (
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else "OK"
                ),
            }
        else:
            return {
                "status": "🟡 Degraded",
                "healthy": False,
                "response_time": response.elapsed.total_seconds(),
                "details": f"HTTP {response.status_code}",
            }
    except requests.exceptions.Timeout:
        return {
            "status": "🟡 Timeout",
            "healthy": False,
            "response_time": timeout,
            "details": "Request timed out",
        }
    except requests.exceptions.ConnectionError:
        return {
            "status": "🔴 Offline",
            "healthy": False,
            "response_time": None,
            "details": "Cannot connect to service",
        }
    except Exception as e:
        return {
            "status": "🔴 Error",
            "healthy": False,
            "response_time": None,
            "details": str(e),
        }


def get_system_status() -> Dict:
    """Get the overall system status"""
    services = {
        "Optimizer": "http://optimizer:5050/health",
        "Search Engine": "http://search-engine:5150/health",
        "LLM Dispatcher": "http://llm-dispatcher:5100/health",
        "Scraper": "http://scraper:5200/health",
        "RAG Builder": "http://rag-builder:5300/health",
        "ChromaDB": "http://chromadb:8000/api/v2/heartbeat",
    }

    status_results = {}
    overall_healthy = True

    for service_name, url in services.items():
        status_results[service_name] = check_service_health(service_name, url)
        if not status_results[service_name]["healthy"]:
            overall_healthy = False

    return {
        "services": status_results,
        "overall_status": (
            "🟢 All Systems Operational" if overall_healthy else "🟡 System Degraded"
        ),
        "healthy": overall_healthy,
        "timestamp": time.time(),
    }


def display_system_status():
    """Display system status in the UI"""
    with st.expander("🔧 System Status", expanded=False):
        status = get_system_status()

        # Overall status
        st.markdown(f"**Overall Status:** {status['overall_status']}")

        # Service status grid
        cols = st.columns(2)
        for i, (service_name, service_status) in enumerate(status["services"].items()):
            with cols[i % 2]:
                st.metric(
                    service_name,
                    service_status["status"],
                    help=f"Response time: {service_status.get('response_time', 'N/A')}s\nDetails: {service_status['details']}",
                )

        # Refresh button
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()


def check_system_readiness() -> bool:
    """Check if the system is ready to process queries"""
    status = get_system_status()

    # Check if critical services are healthy
    critical_services = ["Optimizer", "Search Engine", "LLM Dispatcher"]
    critical_healthy = all(
        status["services"].get(service, {}).get("healthy", False)
        for service in critical_services
    )

    return critical_healthy
