import sys
import sqlite3
sys.modules["sqlite3"] = sqlite3

import streamlit as st
import os
import sys
from datetime import datetime
from pathlib import Path
import json
import pandas as pd
import re

from src.components.sidebar import render_sidebar
from src.components.output_handler import capture_output
from src.lead_generator.crew import LeadGenerator
from src.utils.pricing import ModelsPricing



# Set page configuration
st.set_page_config(
    page_title="AI Lead Generator",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Header with centered title
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    # Center the main title using markdown with HTML
    st.markdown("<h1 style='text-align: center;'>🔍 AI Lead Generator </h1>", unsafe_allow_html=True)

# Render sidebar and get user configuration
config = render_sidebar()

# Create 3 columns with the middle one being wider
left_col, center_col, right_col = st.columns([1, 2, 1])

# Use the center column for all our content
with center_col:
    # First section: "Start Your Research" (now centered)
    st.markdown("<h2 style='text-align: center;'>Start Your Research</h2>", unsafe_allow_html=True)
    
    # Market research topic input - connected to session state
    if 'topic' not in st.session_state:
        st.session_state.topic = ""
        
    industry = st.text_input(
        "Enter a industry to research",
        placeholder="e.g., AI LLMs, Renewable Energy, FinTech",
        help="Specify the industry you want to explore for potential leads",
        key="industry"  # This links the input to st.session_state.industry
    )
    
    country = st.text_input(
        "Enter a country to research",
        placeholder="e.g., United States, United Kingdom, Canada",
        help="Specify the country you want to explore for potential leads",
        key="country"  # This links the input to st.session_state.country
    )

    # Example topics that users can click
    st.write("Or try one of these examples:")
    example_col1, example_col2, example_col3 = st.columns(3)
    
    # Define example topics
    examples = [
        "AI-powered SaaS platforms",
        "Renewable Energy Startups",
        "FinTech Payment Solutions"
    ]
    
    # Define click handler function
    def set_example_topic(example):
        st.session_state.industry = example  # Update industry instead of topic
        
    # Add a button for each example
    with example_col1:
        st.button(examples[0], on_click=set_example_topic, args=(examples[0],), key="example1")
        
    with example_col2:
        st.button(examples[1], on_click=set_example_topic, args=(examples[1],), key="example2")
        
    with example_col3:
        st.button(examples[2], on_click=set_example_topic, args=(examples[2],), key="example3")
    
    # Generate button
    run_button = st.button("🚀 Generate Leads", type="primary", use_container_width=True)
    
    # Add a small space
    st.write("")
    
    # Second section: "Why Use AI-Powered Lead Generation?" in expandable block
    with st.expander("Why Use AI-Powered Lead Generation?"):
        st.subheader("⚡ Speed & Efficiency")
        st.write("Generate leads 10x faster than manual methods")
        
        st.subheader("🎯 Precision Targeting")
        st.write("Identify prospects that match your ideal customer profile")
        
        st.subheader("📊 Data-Driven Insights")
        st.write("Make informed decisions based on comprehensive research")

# Results area (initially hidden)
results_container = st.container()

# Initialize session state for persistent storage
if 'results' not in st.session_state:
    st.session_state.results = None
if 'pricing_tracker' not in st.session_state:
    st.session_state.pricing_tracker = ModelsPricing()

# Update the run button section to preserve state
if run_button:
    if not industry or not country:
        st.error("Please enter an industry and country")
    elif not os.environ.get("OPENAI_API_KEY"):
        st.warning("⚠️ Please enter your OpenAI API key in the sidebar to continue")
    else:
        with st.status("🤖 Researching... This may take several minutes.", expanded=True) as status:
            try:
                # Initialize the crew
                lead_gen_crew = LeadGenerator().crew()
                
                # Run the crew with industry and country inputs
                results = lead_gen_crew.kickoff(inputs={
                    "industry": industry,
                    "country": country
                })
                
                # Store results in session state immediately
                st.session_state.results = results
                status.update(label="✅ Lead generation completed!", state="complete", expanded=False)
                
                # Now let's process the results first
                with results_container:
                    st.success("✅ Lead generation process completed successfully!")
                    
                    st.markdown("### Your Leads are ready!")
                    
                    try:
                        # Get the results from the CrewOutput object
                        results = st.session_state.results
                        
                        # Try to get the last task's output
                        if hasattr(results, 'tasks_output') and results.tasks_output:
                            last_task = results.tasks_output[-1]
                            if hasattr(last_task, 'raw'):
                                results_list = json.loads(last_task.raw)
                            else:
                                # Fallback to raw attribute if it exists
                                results_list = json.loads(results.raw) if hasattr(results, 'raw') else []
                        else:
                            # If no tasks_output, try raw directly
                            results_list = json.loads(results.raw) if hasattr(results, 'raw') else []

                        if not results_list:
                            st.warning("No leads were found in the results")
                            st.stop()

                        # Create metrics summary
                        total_leads = len(results_list)
                        avg_score = sum(float(lead.get('score', 0)) for lead in results_list if isinstance(lead, dict)) / total_leads if total_leads > 0 else 0
                        
                        # Display metrics summary
                        metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
                        with metrics_col1:
                            st.metric("Total Leads", f"{total_leads}")
                        with metrics_col2:
                            st.metric("Average Score", f"{avg_score:.1f}/10")
                        with metrics_col3:
                            st.metric("High-Quality Leads", f"{sum(1 for lead in results_list if isinstance(lead, dict) and float(lead.get('score', 0)) >= 7)}")

                        # Sort leads by score (highest first)
                        results_list = sorted(
                            results_list,
                            key=lambda x: float(x.get('score', 0)) if isinstance(x, dict) else 0,
                            reverse=True
                        )

                        # Display each lead in a structured format
                        for idx, lead in enumerate(results_list, 1):
                            if not isinstance(lead, dict):
                                continue
                            
                            # Create an expander for each company
                            with st.expander(f"🏢 {idx}. {lead.get('company_name', 'Unknown Company')} (Score: {lead.get('score', 'N/A')}/10)", expanded=False):
                                # Company header with score-based color
                                score = float(lead.get('score', 0))
                                if score >= 8:
                                    header_color = "green"
                                elif score >= 6:
                                    header_color = "orange"
                                else:
                                    header_color = "gray"
                                
                                st.markdown(f"<h3 style='color: {header_color};'>{lead.get('company_name', 'N/A')}</h3>", unsafe_allow_html=True)
                                
                                col1, col2 = st.columns([3, 2])
                                
                                with col1:
                                    st.markdown("#### Company Information")
                                    st.markdown(f"**Annual Revenue:** {lead.get('annual_revenue', 'N/A')}")
                                    
                                    location = lead.get('location', {})
                                    if isinstance(location, dict):
                                        st.markdown(f"**Location:** {location.get('city', 'N/A')}, {location.get('country', 'N/A')}")
                                    else:
                                        st.markdown(f"**Location:** {location or 'N/A'}")
                                    
                                    website = lead.get('website_url', 'N/A')
                                    st.markdown(f"**Website:** [{website}]({website})" if website != 'N/A' else "**Website:** N/A")
                                    st.markdown(f"**Number of Employees:** {lead.get('num_employees', 'N/A')}")
                                
                                with col2:
                                    st.markdown("#### Company Profile")
                                    st.markdown(f"**Match Score:** {lead.get('score', 'N/A')}/10")
                                    st.progress(float(lead.get('score', 0)) / 10)
                                
                                st.markdown("#### Business Overview")
                                st.markdown(lead['review'] if 'review' in lead else 'N/A')
                                
                                if 'recommendations' in lead:
                                    st.markdown("#### Recommendations")
                                    st.markdown(lead['recommendations'])
                                
                                # Display key decision makers in markdown format
                                kdm = lead['key_decision_makers'] if 'key_decision_makers' in lead else []
                                if kdm:
                                    st.markdown("#### Key Decision Makers")
                                    for person in kdm:
                                        if isinstance(person, dict):
                                            name = person['name'] if 'name' in person else 'N/A'
                                            role = person['role'] if 'role' in person else 'N/A'
                                            linkedin = person['linkedin'] if 'linkedin' in person else '#'
                                            
                                            linkedin_link = f"[LinkedIn Profile]({linkedin})" if linkedin != '#' else 'N/A'
                                            st.markdown(f"**{name}** - {role} ({linkedin_link})")

                        # Add a JSON view option at the bottom
                        with st.expander("🔍 View Raw Data", expanded=False):
                            st.json(results_list)

                    except Exception as e:
                        st.error(f"Error displaying results: {str(e)}")
                        st.code(str(st.session_state.results), language='json')
                    
                    # Download section
                    st.markdown("### 📥 Download Research Report")
                    try:
                        # Prepare markdown report
                        download_data = "# Lead Generation Report\n\n"
                        for lead in results_list:
                            download_data += f"## {lead.get('company_name', 'N/A')}\n\n"
                            download_data += f"- **Annual Revenue:** {lead.get('annual_revenue', 'N/A')}\n"
                            download_data += f"- **Website:** {lead.get('website_url', 'N/A')}\n"
                            download_data += f"- **Review:** {lead.get('review', 'N/A')}\n"
                            download_data += f"- **Number of Employees:** {lead.get('num_employees', 'N/A')}\n"
                            download_data += f"- **Score:** {lead.get('score', 'N/A')}/10\n\n"
                            
                            # Add key decision makers
                            kdm = lead.get('key_decision_makers', [])
                            if kdm:
                                download_data += "### Key Decision Makers\n"
                                for person in kdm:
                                    if isinstance(person, dict):
                                        download_data += f"- {person.get('name', 'N/A')} ({person.get('role', 'N/A')}): {person.get('linkedin', 'N/A')}\n"
                                download_data += "\n"
                            
                            download_data += "---\n\n"
                        
                        # Also include raw JSON data at the end
                        download_data += "\n## Raw JSON Data\n\n```json\n"
                        download_data += json.dumps(results_list, indent=2)
                        download_data += "\n```\n"
                        
                    except Exception as e:
                        download_data = f"Error generating report: {str(e)}"
                    
                    st.download_button(
                        label="Download Full Report",
                        data=download_data,
                        file_name=f"lead_generation_report_{industry}_{country}.md",
                        mime="text/plain"
                    )

                    # Usage metrics section - immediately after results and download
                    st.markdown("### 💰 Usage Metrics")
                    
                    try:
                        # Check for usage metrics directly on the crew object (live, not from state)
                        if hasattr(lead_gen_crew, 'usage_metrics'):
                            metrics = lead_gen_crew.usage_metrics
                            
                            # First, let's display what we're dealing with for debugging
                            #st.write(f"Metrics type: {type(metrics)}")
                            metrics_str = str(metrics)
                            #st.write(f"Metrics value: {metrics_str}")
                            
                            # Parse the metrics - whether it's a string directly or a UsageMetrics object with string representation
                            metrics_dict = {}
                            parse_string = metrics_str
                            
                            # Split by space and extract key-value pairs
                            for item in parse_string.split():
                                if "=" in item:
                                    key, value = item.split("=")
                                    try:
                                        metrics_dict[key] = int(value)
                                    except ValueError:
                                        metrics_dict[key] = value
                            
                            # Display the parsed metrics
                            with st.expander("🔍 Parsed Metrics", expanded=False):
                                st.json(metrics_dict)
                            
                            # Extract relevant token counts
                            input_tokens = metrics_dict.get('prompt_tokens', 0)
                            output_tokens = metrics_dict.get('completion_tokens', 0)
                            total_tokens = metrics_dict.get('total_tokens', 0)
                            
                            # Calculate approximate cost based on gpt-4 rates
                            # $0.03/1K input tokens, $0.06/1K output tokens
                            input_cost = (input_tokens / 1000000) * 0.015
                            output_cost = (output_tokens / 1000000) * 0.06
                            total_cost = input_cost + output_cost
                            
                            # Update the pricing tracker
                            st.session_state.pricing_tracker.track_usage(
                                input_tokens=input_tokens,
                                output_tokens=output_tokens
                            )
                            
                            # Display metrics in a user-friendly way
                            #st.success("Usage metrics processed successfully")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Cost", f"${total_cost:.4f}")
                            with col2:
                                st.metric("Input Tokens", f"{input_tokens:,}")
                            with col3:
                                st.metric("Output Tokens", f"{output_tokens:,}")
                            
                        # Try token_usage as fallback
                        elif hasattr(results, 'token_usage') and results.token_usage:
                            token_usage = results.token_usage
                            
                            # Display the token usage data
                            with st.expander("🔍 Token Usage Data", expanded=False):
                                st.write(token_usage)
                            
                            # Update the pricing tracker
                            if isinstance(token_usage, dict):
                                input_tokens = token_usage.get('total_prompt_tokens', 0)
                                output_tokens = token_usage.get('total_completion_tokens', 0)
                                
                                st.session_state.pricing_tracker.track_usage(
                                    input_tokens=input_tokens,
                                    output_tokens=output_tokens
                                )
                                
                                usage_summary = st.session_state.pricing_tracker.get_usage_summary()
                                
                                # Display metrics in a user-friendly way
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total Cost", f"${usage_summary['total_cost']:.4f}")
                                with col2:
                                    st.metric("Input Tokens", f"{usage_summary['input_tokens']:,}")
                                with col3:
                                    st.metric("Output Tokens", f"{usage_summary['output_tokens']:,}")
                        else:
                            st.info("No usage metrics available for this run")
                            
                    except Exception as cost_error:
                        st.warning(f"Usage metrics calculation error: {str(cost_error)}")
                        st.warning("This doesn't affect your results, just the usage tracking.")
                        with st.expander("Error Details", expanded=False):
                            import traceback
                            st.code(traceback.format_exc())

            except Exception as e:
                status.update(label="❌ Error occurred", state="error")
                st.error(f"An error occurred: {str(e)}")
                st.stop()
                
# Remove the duplicate results handling code
if __name__ == "__main__":
    # This is only used when running the script directly
    pass

# Add footer
footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
with footer_col2:
    st.caption("Made with ❤️ using AI-powered lead generation technology")




# import streamlit as st
# import pandas as pd
# import math
# import io
# import re
# from typing import Dict, List, Tuple, Optional, Any
# from dataclasses import dataclass
# from enum import Enum

# try:
#     from gerbonara.excellon import ExcellonFile
#     from gerbonara.rs274x import GerberFile
#     from gerbonara.ipc356 import Netlist, PadType
#     from gerbonara.graphic_objects import Flash, Line, Arc
#     from gerbonara.cam import FileSettings
#     from gerbonara.utils import MM, Inch
#     GERBONARA_AVAILABLE = True
# except ImportError:
#     GERBONARA_AVAILABLE = False
#     st.error("Gerbonara library not found. Please install it using: pip install gerbonara")

# # Data classes for better structure
# @dataclass
# class DrillHole:
#     x: float
#     y: float
#     diameter: float
#     plated: Optional[bool]
#     tool_number: str
#     source_file: str

# @dataclass
# class ArtworkPad:
#     x: float
#     y: float
#     shape: str
#     parameters: Dict[str, Any]
#     aperture_id: str
#     layer_type: str
#     source_file: str

# @dataclass
# class TestPoint:
#     x: float
#     y: float
#     net_name: str
#     ref_des: str
#     pin: str
#     pad_type: str
#     is_via: bool
#     hole_diameter: Optional[float]
#     source_file: str

# @dataclass
# class ConsolidatedTestPoint:
#     x: float
#     y: float
#     net_name: str
#     ref_des: str
#     pin: str
#     test_point_designation: str
#     hole_diameter: Optional[float]
#     pad_details: Optional[Dict]
#     side: str
#     accessibility: str
#     source_files: Dict[str, str]
#     validation_status: str

# class LayerType(Enum):
#     TOP_COPPER = "top_copper"
#     BOTTOM_COPPER = "bottom_copper"
#     TOP_SOLDERMASK = "top_soldermask"
#     BOTTOM_SOLDERMASK = "bottom_soldermask"
#     TOP_PASTE = "top_paste"
#     BOTTOM_PASTE = "bottom_paste"
#     DRILL = "drill"
#     OUTLINE = "outline"
#     UNKNOWN = "unknown"

# class CADFileProcessor:
#     def __init__(self):
#         self.drill_holes: List[DrillHole] = []
#         self.artwork_pads: List[ArtworkPad] = []
#         self.test_points: List[TestPoint] = []
#         self.consolidated_points: List[ConsolidatedTestPoint] = []
#         self.validation_messages: List[Dict] = []
#         self.coordinate_tolerance = 0.01  # 10 microns in mm
        
#     def clear_data(self):
#         """Clear all stored data for new processing session"""
#         self.drill_holes.clear()
#         self.artwork_pads.clear()
#         self.test_points.clear()
#         self.consolidated_points.clear()
#         self.validation_messages.clear()
    
#     def determine_layer_type(self, filename: str) -> LayerType:
#         """Determine layer type based on filename patterns"""
#         filename_lower = filename.lower()
        
#         # Cadence layer naming patterns
#         if any(ext in filename_lower for ext in ['.ast', '.spt']):
#             return LayerType.TOP_COPPER
#         elif any(ext in filename_lower for ext in ['.asb', '.spb']):
#             return LayerType.BOTTOM_COPPER
#         elif any(ext in filename_lower for ext in ['.smc', '.smt']):
#             return LayerType.TOP_SOLDERMASK
#         elif any(ext in filename_lower for ext in ['.sms', '.smb']):
#             return LayerType.BOTTOM_SOLDERMASK
#         elif any(ext in filename_lower for ext in ['.cpt', '.spt']):
#             return LayerType.TOP_PASTE
#         elif any(ext in filename_lower for ext in ['.cpb', '.spb']):
#             return LayerType.BOTTOM_PASTE
#         elif '.drl' in filename_lower:
#             return LayerType.DRILL
#         elif 'outline' in filename_lower or 'board' in filename_lower:
#             return LayerType.OUTLINE
#         elif re.search(r'\.l\d+[np]', filename_lower):
#             # Layer files like L02N, L03P etc.
#             if filename_lower.endswith('p'):
#                 return LayerType.TOP_COPPER
#             else:
#                 return LayerType.BOTTOM_COPPER
#         else:
#             return LayerType.UNKNOWN
    
#     def process_drill_file(self, file_content: str, filename: str) -> bool:
#         """Process Excellon drill files (.drl)"""
#         try:
#             excellon_file = ExcellonFile.from_string(file_content)
            
#             if not excellon_file.objects:
#                 self.validation_messages.append({
#                     'type': 'warning',
#                     'message': f"No drill objects found in {filename}",
#                     'details': {'file': filename}
#                 })
#                 return False
            
#             # Process drill holes
#             for obj in excellon_file.objects:
#                 if hasattr(obj, 'x') and hasattr(obj, 'y') and hasattr(obj, 'tool'):
#                     tool = obj.tool
#                     drill_hole = DrillHole(
#                         x=round(obj.x, 4),
#                         y=round(obj.y, 4),
#                         diameter=round(tool.diameter, 4),
#                         plated=tool.plated,
#                         tool_number=str(tool.name) if tool.name else f"T{len(self.drill_holes)+1}",
#                         source_file=filename
#                     )
#                     self.drill_holes.append(drill_hole)
            
#             return True
            
#         except Exception as e:
#             self.validation_messages.append({
#                 'type': 'error',
#                 'message': f"Error processing drill file {filename}: {str(e)}",
#                 'details': {'file': filename, 'error': str(e)}
#             })
#             return False
    
#     def process_gerber_file(self, file_content: str, filename: str) -> bool:
#         """Process Gerber artwork files (.art and layer files)"""
#         try:
#             gerber_file = GerberFile.from_string(file_content)
#             layer_type = self.determine_layer_type(filename)
            
#             if not gerber_file.objects:
#                 self.validation_messages.append({
#                     'type': 'info',
#                     'message': f"No objects found in {filename} - might be outline or reference layer",
#                     'details': {'file': filename}
#                 })
#                 return True
            
#             # Process flash objects (pads)
#             for obj in gerber_file.objects:
#                 if isinstance(obj, Flash):
#                     aperture = obj.aperture
                    
#                     # Extract aperture parameters
#                     params = {}
#                     shape = "unknown"
                    
#                     if hasattr(aperture, 'shape'):
#                         shape = aperture.shape
#                         if shape == 'circle':
#                             params['diameter'] = round(aperture.diameter, 4)
#                         elif shape in ['rectangle', 'obround']:
#                             params['width'] = round(aperture.width, 4)
#                             params['height'] = round(aperture.height, 4)
#                             if hasattr(aperture, 'corner_radius'):
#                                 params['corner_radius'] = round(aperture.corner_radius, 4)
#                         elif shape == 'polygon':
#                             params['outer_diameter'] = round(aperture.outer_diameter, 4)
#                             params['vertices'] = aperture.n_vertices
#                     else:
#                         # Handle standard apertures
#                         shape = str(aperture).split(' ')[0] if str(aperture) else "standard"
#                         if hasattr(aperture, 'diameter'):
#                             params['diameter'] = round(aperture.diameter, 4)
                    
#                     artwork_pad = ArtworkPad(
#                         x=round(obj.x, 4),
#                         y=round(obj.y, 4),
#                         shape=shape,
#                         parameters=params,
#                         aperture_id=str(obj.aperture_id) if hasattr(obj, 'aperture_id') else "unknown",
#                         layer_type=layer_type.value,
#                         source_file=filename
#                     )
#                     self.artwork_pads.append(artwork_pad)
            
#             return True
            
#         except Exception as e:
#             self.validation_messages.append({
#                 'type': 'error',
#                 'message': f"Error processing Gerber file {filename}: {str(e)}",
#                 'details': {'file': filename, 'error': str(e)}
#             })
#             return False
    
#     def process_ipc_file(self, file_content: str, filename: str) -> bool:
#         """Process IPC-356 netlist files (.ipc)"""
#         try:
#             ipc_netlist = Netlist.from_string(file_content)
            
#             if not ipc_netlist.test_records:
#                 self.validation_messages.append({
#                     'type': 'warning',
#                     'message': f"No test records found in {filename}",
#                     'details': {'file': filename}
#                 })
#                 return False
            
#             # Process test records
#             for record in ipc_netlist.test_records:
#                 test_point = TestPoint(
#                     x=round(record.x, 4),
#                     y=round(record.y, 4),
#                     net_name=record.net_name or "UNNAMED",
#                     ref_des=record.ref_des or "UNKNOWN",
#                     pin=str(record.pin_num) if record.pin_num else "0",
#                     pad_type=record.pad_type.name if record.pad_type else "UNKNOWN",
#                     is_via=record.is_via,
#                     hole_diameter=round(record.hole_dia, 4) if record.hole_dia else None,
#                     source_file=filename
#                 )
#                 self.test_points.append(test_point)
            
#             return True
            
#         except Exception as e:
#             self.validation_messages.append({
#                 'type': 'error',
#                 'message': f"Error processing IPC file {filename}: {str(e)}",
#                 'details': {'file': filename, 'error': str(e)}
#             })
#             return False
    
#     def process_ipc_text_file(self, file_content: str, filename: str) -> bool:
#         """Process IPC-356 files with .txt extension"""
#         try:
#             # Check if content looks like IPC-356 format
#             lines = file_content.strip().split('\n')
#             ipc_indicators = ['C  ', 'P  ', 'V  ', 'M  ']
            
#             if not any(any(line.startswith(indicator) for indicator in ipc_indicators) for line in lines[:20]):
#                 self.validation_messages.append({
#                     'type': 'warning',
#                     'message': f"File {filename} doesn't appear to be IPC-356 format",
#                     'details': {'file': filename}
#                 })
#                 return False
            
#             # Parse IPC-356 format manually
#             test_point_count = 0
#             for line in lines:
#                 line = line.strip()
#                 if line.startswith('P  '):  # Pad record
#                     try:
#                         # IPC-356 pad record format: P  pad_name net_name x y side layer
#                         parts = line.split()
#                         if len(parts) >= 6:
#                             x = float(parts[3]) / 1000.0  # Convert from mils to mm
#                             y = float(parts[4]) / 1000.0
#                             net_name = parts[2] if parts[2] != '-' else "UNNAMED"
#                             ref_des = parts[1].split('-')[0] if '-' in parts[1] else parts[1]
#                             pin = parts[1].split('-')[1] if '-' in parts[1] else "1"
                            
#                             test_point = TestPoint(
#                                 x=round(x, 4),
#                                 y=round(y, 4),
#                                 net_name=net_name,
#                                 ref_des=ref_des,
#                                 pin=pin,
#                                 pad_type="SMD",
#                                 is_via=False,
#                                 hole_diameter=None,
#                                 source_file=filename
#                             )
#                             self.test_points.append(test_point)
#                             test_point_count += 1
#                     except (ValueError, IndexError) as e:
#                         continue  # Skip malformed lines
                
#                 elif line.startswith('V  '):  # Via record
#                     try:
#                         parts = line.split()
#                         if len(parts) >= 5:
#                             x = float(parts[2]) / 1000.0
#                             y = float(parts[3]) / 1000.0
#                             net_name = parts[1] if parts[1] != '-' else "UNNAMED"
                            
#                             test_point = TestPoint(
#                                 x=round(x, 4),
#                                 y=round(y, 4),
#                                 net_name=net_name,
#                                 ref_des="VIA",
#                                 pin="0",
#                                 pad_type="VIA",
#                                 is_via=True,
#                                 hole_diameter=None,
#                                 source_file=filename
#                             )
#                             self.test_points.append(test_point)
#                             test_point_count += 1
#                     except (ValueError, IndexError) as e:
#                         continue
            
#             if test_point_count > 0:
#                 self.validation_messages.append({
#                     'type': 'info',
#                     'message': f"Successfully parsed {test_point_count} test points from {filename}",
#                     'details': {'file': filename, 'count': test_point_count}
#                 })
#                 return True
#             else:
#                 self.validation_messages.append({
#                     'type': 'warning',
#                     'message': f"No valid test points found in {filename}",
#                     'details': {'file': filename}
#                 })
#                 return False
                
#         except Exception as e:
#             self.validation_messages.append({
#                 'type': 'error',
#                 'message': f"Error processing IPC text file {filename}: {str(e)}",
#                 'details': {'file': filename, 'error': str(e)}
#             })
#             return False
    
#     def find_closest_match(self, x: float, y: float, items: List, tolerance: float) -> Optional[Any]:
#         """Find closest matching item within tolerance"""
#         closest_item = None
#         min_distance = float('inf')
        
#         for item in items:
#             item_x = item.x if hasattr(item, 'x') else item['x']
#             item_y = item.y if hasattr(item, 'y') else item['y']
            
#             distance = math.sqrt((x - item_x)**2 + (y - item_y)**2)
#             if distance <= tolerance and distance < min_distance:
#                 min_distance = distance
#                 closest_item = item
        
#         return closest_item
    
#     def determine_accessibility(self, test_point: TestPoint, matched_pads: List[ArtworkPad], 
#                               matched_hole: Optional[DrillHole]) -> Tuple[str, str]:
#         """Determine test point side and accessibility for bed-of-nails testing"""
#         side = "Unknown"
#         accessibility = "None"
        
#         if test_point.is_via or test_point.pad_type == "VIA":
#             side = "Through-hole"
#             accessibility = "Both" if matched_hole and matched_hole.plated else "Mechanical"
#         else:
#             # Check pad layers to determine side
#             top_pads = [p for p in matched_pads if 'top' in p.layer_type]
#             bottom_pads = [p for p in matched_pads if 'bottom' in p.layer_type]
            
#             if top_pads and bottom_pads:
#                 side = "Both"
#                 accessibility = "Both"
#             elif top_pads:
#                 side = "Top"
#                 accessibility = "Top"
#             elif bottom_pads:
#                 side = "Bottom"
#                 accessibility = "Bottom"
#             else:
#                 side = "SMD"
#                 accessibility = "Single"
        
#         return side, accessibility
    
#     def consolidate_test_points(self) -> bool:
#         """Consolidate test points with matching pads and holes"""
#         if not self.test_points:
#             self.validation_messages.append({
#                 'type': 'warning',
#                 'message': "No test points found for consolidation",
#                 'details': {}
#             })
#             return False
        
#         self.consolidated_points.clear()
        
#         for test_point in self.test_points:
#             # Find matching pads
#             matched_pads = []
#             for pad in self.artwork_pads:
#                 if self.find_closest_match(test_point.x, test_point.y, [pad], self.coordinate_tolerance):
#                     matched_pads.append(pad)
            
#             # Find matching hole
#             matched_hole = self.find_closest_match(test_point.x, test_point.y, self.drill_holes, self.coordinate_tolerance)
            
#             # Determine accessibility
#             side, accessibility = self.determine_accessibility(test_point, matched_pads, matched_hole)
            
#             # Create consolidated test point
#             consolidated = ConsolidatedTestPoint(
#                 x=test_point.x,
#                 y=test_point.y,
#                 net_name=test_point.net_name,
#                 ref_des=test_point.ref_des,
#                 pin=test_point.pin,
#                 test_point_designation=f"{test_point.ref_des}-{test_point.pin}",
#                 hole_diameter=matched_hole.diameter if matched_hole else test_point.hole_diameter,
#                 pad_details={'pads': [{'shape': p.shape, 'params': p.parameters, 'layer': p.layer_type} for p in matched_pads]} if matched_pads else None,
#                 side=side,
#                 accessibility=accessibility,
#                 source_files={
#                     'ipc': test_point.source_file,
#                     'art': matched_pads[0].source_file if matched_pads else None,
#                     'drl': matched_hole.source_file if matched_hole else None
#                 },
#                 validation_status=self.validate_test_point(test_point, matched_pads, matched_hole)
#             )
            
#             self.consolidated_points.append(consolidated)
        
#         return True
    
#     def validate_test_point(self, test_point: TestPoint, matched_pads: List[ArtworkPad], 
#                           matched_hole: Optional[DrillHole]) -> str:
#         """Validate individual test point for bed-of-nails accessibility"""
#         issues = []
        
#         # Check for missing pad
#         if not matched_pads:
#             issues.append("No matching pad found")
        
#         # Check for missing hole when expected
#         if (test_point.is_via or test_point.pad_type in ["THROUGH_HOLE", "VIA"]) and not matched_hole:
#             issues.append("Expected drill hole not found")
        
#         # Check hole plating for through-holes
#         if matched_hole and test_point.pad_type == "THROUGH_HOLE" and not matched_hole.plated:
#             issues.append("Through-hole not plated")
        
#         # Check accessibility for bed-of-nails
#         if not matched_pads and not matched_hole:
#             issues.append("Not accessible for probing")
        
#         if issues:
#             return f"Issues: {'; '.join(issues)}"
#         else:
#             return "Valid"

# def main():
#     st.set_page_config(
#         page_title="CAD Test Point Extractor",
#         page_icon="🔧",
#         layout="wide"
#     )
    
#     st.title("🔧 CAD Test Point Extractor for Bed-of-Nails Testing")
#     st.markdown("Extract and analyze test points from Cadence CAD files for bed-of-nails test fixture design")
    
#     if not GERBONARA_AVAILABLE:
#         st.stop()
    
#     # Initialize processor
#     if 'processor' not in st.session_state:
#         st.session_state.processor = CADFileProcessor()
    
#     processor = st.session_state.processor
    
#     # Sidebar configuration
#     with st.sidebar:
#         st.header("Configuration")
        
#         tolerance = st.number_input(
#             "Coordinate Tolerance (mm)",
#             min_value=0.001,
#             max_value=1.0,
#             value=0.01,
#             step=0.001,
#             format="%.3f",
#             help="Tolerance for matching coordinates between files"
#         )
#         processor.coordinate_tolerance = tolerance
        
#         st.header("Supported File Types")
#         file_types = [
#             "Drill files: .drl",
#             "Gerber artwork: .art, .AST, .ASB",
#             "Copper layers: .L##N, .L##P",
#             "Solder mask: .SMC, .SMS",
#             "Paste mask: .CPT, .CSP",
#             "IPC netlist: .ipc, .ipc.txt",
#             "Fabrication: .FAB",
#             "Silkscreen: .SKC, .SKS"
#         ]
#         for file_type in file_types:
#             st.markdown(f"• {file_type}")
    
#     # File upload
#     uploaded_files = st.file_uploader(
#         "Upload CAD Files",
#         accept_multiple_files=True,
#         type=[
#             "ASB", "AST", "CPT", "CSP", "FAB", "ipc", "SKC", "SKS",
#             "SMC", "SMS", "SPT", "SSP", "drl", "art", "L02N", "L03P",
#             "L04N", "L05P", "L06N", "L07P", "L08N", "L09N", "L10N",
#             "L11N", "L12P", "L13N", "L14P", "L15N", "L16P", "L17N",
#             "txt"
#         ],
#         help="Upload your Cadence CAD files for analysis"
#     )
    
#     if uploaded_files:
#         # Clear previous data
#         processor.clear_data()
        
#         # Process files
#         progress_bar = st.progress(0)
#         status_text = st.empty()
        
#         for i, uploaded_file in enumerate(uploaded_files):
#             progress = (i + 1) / len(uploaded_files)
#             progress_bar.progress(progress)
#             status_text.text(f"Processing {uploaded_file.name}...")
            
#             try:
#                 file_content = uploaded_file.getvalue().decode("utf-8")
#                 filename = uploaded_file.name.lower()
                
#                 if filename.endswith(".drl"):
#                     processor.process_drill_file(file_content, uploaded_file.name)
#                 elif filename.endswith((".art", ".ast", ".asb", ".smc", ".sms", ".cpt", ".csp", ".skc", ".sks")) or \
#                      re.search(r'\.l\d+[np]$', filename):
#                     processor.process_gerber_file(file_content, uploaded_file.name)
#                 elif filename.endswith(".ipc"):
#                     processor.process_ipc_file(file_content, uploaded_file.name)
#                 elif filename.endswith(".ipc.txt") or (filename.endswith(".txt") and "ipc" in filename):
#                     processor.process_ipc_text_file(file_content, uploaded_file.name)
#                 else:
#                     # Try to auto-detect file type by content
#                     content_preview = file_content[:1000].upper()
#                     if any(indicator in content_preview for indicator in ['P  ', 'C  ', 'V  ', 'M  ']):
#                         processor.process_ipc_text_file(file_content, uploaded_file.name)
#                     else:
#                         st.info(f"Skipped unsupported file: {uploaded_file.name}")
                    
#             except Exception as e:
#                 processor.validation_messages.append({
#                     'type': 'error',
#                     'message': f"Failed to process {uploaded_file.name}: {str(e)}",
#                     'details': {'file': uploaded_file.name}
#                 })
        
#         progress_bar.empty()
#         status_text.empty()
        
#         # Display processing results
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             st.metric("Drill Holes", len(processor.drill_holes))
#         with col2:
#             st.metric("Artwork Pads", len(processor.artwork_pads))
#         with col3:
#             st.metric("Test Points", len(processor.test_points))
        
#         # Show file processing summary
#         if processor.validation_messages:
#             with st.expander("File Processing Details", expanded=False):
#                 for msg in processor.validation_messages:
#                     if msg['type'] == 'error':
#                         st.error(f"❌ {msg['message']}")
#                     elif msg['type'] == 'warning':
#                         st.warning(f"⚠️ {msg['message']}")
#                     else:
#                         st.info(f"ℹ️ {msg['message']}")
        
#         # Consolidate test points
#         if processor.test_points:
#             st.header("Test Point Analysis")
            
#             if processor.consolidate_test_points():
#                 st.success(f"Successfully consolidated {len(processor.consolidated_points)} test points")
                
#                 # Create detailed report
#                 report_data = []
#                 for point in processor.consolidated_points:
#                     hole_size = f"{point.hole_diameter:.3f} mm" if point.hole_diameter else "N/A"
                    
#                     report_data.append({
#                         "Signal Name": point.net_name,
#                         "Reference Designator": point.ref_des,
#                         "Pin": point.pin,
#                         "Test Point Designation": point.test_point_designation,
#                         "X Coordinate (mm)": f"{point.x:.4f}",
#                         "Y Coordinate (mm)": f"{point.y:.4f}",
#                         "Hole Size": hole_size,
#                         "Side": point.side,
#                         "Accessibility": point.accessibility,
#                         "Status": point.validation_status
#                     })
                
#                 if report_data:
#                     df_report = pd.DataFrame(report_data)
                    
#                     # Filter options
#                     st.subheader("Filter Options")
#                     col1, col2, col3 = st.columns(3)
                    
#                     with col1:
#                         accessibility_filter = st.multiselect(
#                             "Accessibility",
#                             options=df_report["Accessibility"].unique(),
#                             default=df_report["Accessibility"].unique()
#                         )
                    
#                     with col2:
#                         side_filter = st.multiselect(
#                             "Side",
#                             options=df_report["Side"].unique(),
#                             default=df_report["Side"].unique()
#                         )
                    
#                     with col3:
#                         status_filter = st.multiselect(
#                             "Status",
#                             options=df_report["Status"].unique(),
#                             default=df_report["Status"].unique()
#                         )
                    
#                     # Apply filters
#                     filtered_df = df_report[
#                         (df_report["Accessibility"].isin(accessibility_filter)) &
#                         (df_report["Side"].isin(side_filter)) &
#                         (df_report["Status"].isin(status_filter))
#                     ]
                    
#                     st.subheader("Test Point Report")
#                     st.dataframe(filtered_df, use_container_width=True)
                    
#                     # Download options
#                     col1, col2 = st.columns(2)
                    
#                     with col1:
#                         csv_data = filtered_df.to_csv(index=False).encode('utf-8')
#                         st.download_button(
#                             label="📥 Download Filtered Report (CSV)",
#                             data=csv_data,
#                             file_name="test_point_report_filtered.csv",
#                             mime="text/csv"
#                         )
                    
#                     with col2:
#                         full_csv_data = df_report.to_csv(index=False).encode('utf-8')
#                         st.download_button(
#                             label="📥 Download Full Report (CSV)",
#                             data=full_csv_data,
#                             file_name="test_point_report_full.csv",
#                             mime="text/csv"
#                         )
                    
#                     # Summary statistics
#                     st.subheader("Summary Statistics")
#                     col1, col2, col3, col4 = st.columns(4)
                    
#                     with col1:
#                         st.metric("Total Test Points", len(filtered_df))
#                     with col2:
#                         valid_points = len(filtered_df[filtered_df["Status"] == "Valid"])
#                         st.metric("Valid Points", valid_points)
#                     with col3:
#                         top_accessible = len(filtered_df[filtered_df["Accessibility"].str.contains("Top|Both")])
#                         st.metric("Top Accessible", top_accessible)
#                     with col4:
#                         bottom_accessible = len(filtered_df[filtered_df["Accessibility"].str.contains("Bottom|Both")])
#                         st.metric("Bottom Accessible", bottom_accessible)
#         else:
#             st.warning("No test points found in uploaded files. Please check file formats and content.")
    
#     else:
#         st.info("Please upload CAD files to begin analysis")
        
#         # Display sample file structure
#         st.subheader("Expected File Structure")
#         st.code("""
#         📁 CAD Files/
#         ├── 📄 board.drl          # Drill holes
#         ├── 📄 board.art          # Board outline
#         ├── 📄 board.AST          # Top copper layer
#         ├── 📄 board.ASB          # Bottom copper layer
#         ├── 📄 board.SMC          # Top solder mask
#         ├── 📄 board.SMS          # Bottom solder mask
#         ├── 📄 board.ipc          # IPC-356 netlist
#         ├── 📄 board.ipc.txt      # IPC-356 text format
#         └── 📄 board.L##N/P       # Internal layers
#         """)
        
#         st.subheader("Troubleshooting Tips")
#         st.markdown("""
#         **File not being processed?**
#         - Check file extensions - .ipc.txt files are now supported
#         - Ensure IPC-356 files contain proper format indicators (P  , V  , C  )
#         - Files with .txt extension will be auto-detected if they contain IPC-356 content
#         - Check that coordinates are in the expected units (mils will be converted to mm)
        
#         **No test points found?**
#         - Verify IPC-356 file contains pad records (lines starting with 'P  ')
#         - Check that the netlist export included test point information
#         - Ensure file encoding is UTF-8 or ASCII
        
#         **Missing drill or artwork data?**
#         - Upload corresponding .drl files for drill information
#         - Include .art, .AST, .ASB files for pad artwork
#         - Layer files (.L##N, .L##P) provide copper layer information
#         """)
# if __name__ == "__main__":
#     main()






# import streamlit as st
# import pandas as pd
# import numpy as np
# import math
# import io
# import re
# from typing import Dict, List, Tuple, Optional, Any
# from dataclasses import dataclass, field
# from enum import Enum
# import plotly.graph_objects as go
# import plotly.express as px
# from plotly.subplots import make_subplots
# from ollama_client import OllamaClient

# try:
#     from gerbonara.excellon import ExcellonFile
#     from gerbonara.rs274x import GerberFile
#     from gerbonara.ipc356 import Netlist, PadType
#     from gerbonara.graphic_objects import Flash, Line, Arc
#     from gerbonara.cam import FileSettings
#     from gerbonara.utils import MM, Inch
#     GERBONARA_AVAILABLE = True
# except ImportError:
#     GERBONARA_AVAILABLE = False
#     st.error("Gerbonara library not found. Please install it using: pip install gerbonara")

# # Enhanced data classes with additional fields
# @dataclass
# class DrillHole:
#     x: float
#     y: float
#     diameter: float
#     plated: Optional[bool]
#     tool_number: str
#     source_file: str
#     # Enhanced fields
#     tolerance_grade: Optional[str] = None
#     finish: Optional[str] = None

# @dataclass
# class ArtworkPad:
#     x: float
#     y: float
#     shape: str
#     parameters: Dict[str, Any]
#     aperture_id: str
#     layer_type: str
#     source_file: str
#     # Enhanced fields
#     rotation: float = 0.0
#     net_name: Optional[str] = None

# @dataclass
# class TestPoint:
#     x: float
#     y: float
#     net_name: str
#     ref_des: str
#     pin: str
#     pad_type: str
#     is_via: bool
#     hole_diameter: Optional[float]
#     source_file: str
#     # Enhanced fields
#     layer_stack_position: Optional[int] = None
#     electrical_type: Optional[str] = None

# @dataclass
# class ConsolidatedTestPoint:
#     x: float
#     y: float
#     net_name: str
#     ref_des: str
#     pin: str
#     test_point_designation: str
#     hole_diameter: Optional[float]
#     pad_details: Optional[Dict]
#     side: str
#     accessibility: str
#     source_files: Dict[str, str]
#     validation_status: str
#     # Enhanced fields
#     probe_recommendations: Dict[str, Any] = field(default_factory=dict)
#     fixture_requirements: List[str] = field(default_factory=list)
#     test_sequence_priority: int = 0
#     minimum_probe_diameter: Optional[float] = None
#     keepout_zone: Dict[str, float] = field(default_factory=dict)

# class LayerType(Enum):
#     TOP_COPPER = "top_copper"
#     BOTTOM_COPPER = "bottom_copper"
#     TOP_SOLDERMASK = "top_soldermask"
#     BOTTOM_SOLDERMASK = "bottom_soldermask"
#     TOP_PASTE = "top_paste"
#     BOTTOM_PASTE = "bottom_paste"
#     DRILL = "drill"
#     OUTLINE = "outline"
#     INNER_LAYER = "inner_layer"
#     UNKNOWN = "unknown"

# class EnhancedCADFileProcessor:
#     def __init__(self):
#         self.drill_holes: List[DrillHole] = []
#         self.artwork_pads: List[ArtworkPad] = []
#         self.test_points: List[TestPoint] = []
#         self.consolidated_points: List[ConsolidatedTestPoint] = []
#         self.validation_messages: List[Dict] = []
#         self.coordinate_tolerance = 0.01  # 10 microns in mm
#         self.board_outline: List[Tuple[float, float]] = []
#         self.board_thickness = 1.6  # Default PCB thickness in mm
        
#         # Enhanced fixture parameters
#         self.fixture_params = {
#             'min_probe_spacing': 1.27,  # 50 mil minimum spacing
#             'max_probe_density': 0.8,   # probes per mm²
#             'standard_probe_diameters': [0.68, 0.89, 1.02, 1.27, 1.52],  # mm
#             'tooling_hole_tolerance': 0.005,  # mm
#             'fixture_repeatability': 0.025,  # mm
#         }
    
#     def clear_data(self):
#         """Clear all stored data for new processing session"""
#         self.drill_holes.clear()
#         self.artwork_pads.clear()
#         self.test_points.clear()
#         self.consolidated_points.clear()
#         self.validation_messages.clear()
#         self.board_outline.clear()
    
#     def calculate_probe_recommendations(self, point: ConsolidatedTestPoint) -> Dict[str, Any]:
#         """Calculate probe size and fixture recommendations for test point"""
#         recommendations = {
#             'probe_diameter': None,
#             'probe_type': 'standard',
#             'contact_force': 'medium',
#             'special_requirements': []
#         }
        
#         # Determine probe diameter based on hole size or pad size
#         if point.hole_diameter:
#             # For through-holes, probe should be smaller than hole
#             suitable_probes = [d for d in self.fixture_params['standard_probe_diameters'] 
#                              if d < point.hole_diameter * 0.8]
#             if suitable_probes:
#                 recommendations['probe_diameter'] = max(suitable_probes)
#                 recommendations['probe_type'] = 'through_hole'
#             else:
#                 recommendations['special_requirements'].append('Custom probe diameter required')
        
#         elif point.pad_details:
#             # For surface mount pads
#             pad_info = point.pad_details.get('pads', [{}])[0]
#             if 'diameter' in pad_info.get('params', {}):
#                 pad_diameter = pad_info['params']['diameter']
#                 suitable_probes = [d for d in self.fixture_params['standard_probe_diameters'] 
#                                  if d < pad_diameter * 0.6]
#                 if suitable_probes:
#                     recommendations['probe_diameter'] = max(suitable_probes)
#                     recommendations['probe_type'] = 'surface_mount'
#                     recommendations['contact_force'] = 'light'
        
#         # Add special requirements based on accessibility
#         if point.accessibility == 'Bottom':
#             recommendations['special_requirements'].append('Bottom-side fixture required')
#         elif point.accessibility == 'Both':
#             recommendations['special_requirements'].append('Dual-sided testing capability')
        
#         return recommendations
    
#     def calculate_keepout_zones(self, point: ConsolidatedTestPoint) -> Dict[str, float]:
#         """Calculate keepout zones around test point"""
#         keepout = {
#             'probe_clearance': 0.5,  # mm around probe
#             'component_clearance': 1.0,  # mm from components
#             'trace_clearance': 0.2,  # mm from traces
#         }
        
#         # Adjust based on probe type and size
#         if point.probe_recommendations.get('probe_diameter'):
#             probe_radius = point.probe_recommendations['probe_diameter'] / 2
#             keepout['probe_clearance'] = max(keepout['probe_clearance'], probe_radius + 0.2)
        
#         return keepout
    
#     def analyze_fixture_density(self) -> Dict[str, Any]:
#         """Analyze test point density for fixture design"""
#         if not self.consolidated_points:
#             return {}
        
#         # Calculate board area (simplified rectangular approximation)
#         if self.board_outline:
#             x_coords = [p[0] for p in self.board_outline]
#             y_coords = [p[1] for p in self.board_outline]
#             board_area = (max(x_coords) - min(x_coords)) * (max(y_coords) - min(y_coords))
#         else:
#             # Estimate from test point distribution
#             x_coords = [p.x for p in self.consolidated_points]
#             y_coords = [p.y for p in self.consolidated_points]
#             board_area = (max(x_coords) - min(x_coords)) * (max(y_coords) - min(y_coords))
        
#         density_analysis = {
#             'total_points': len(self.consolidated_points),
#             'board_area_mm2': board_area,
#             'point_density': len(self.consolidated_points) / board_area if board_area > 0 else 0,
#             'recommended_max_density': self.fixture_params['max_probe_density'],
#             'density_status': 'optimal',
#             'fixture_recommendations': []
#         }
        
#         # Evaluate density
#         if density_analysis['point_density'] > self.fixture_params['max_probe_density']:
#             density_analysis['density_status'] = 'high'
#             density_analysis['fixture_recommendations'].extend([
#                 'Consider selective testing strategy',
#                 'Use multiple test passes',
#                 'Implement probe grouping'
#             ])
#         elif density_analysis['point_density'] < 0.1:
#             density_analysis['density_status'] = 'low'
#             density_analysis['fixture_recommendations'].append('Standard fixture suitable')
        
#         return density_analysis
    
#     def generate_fixture_report(self) -> Dict[str, Any]:
#         """Generate comprehensive fixture design report"""
#         if not self.consolidated_points:
#             return {}
        
#         # Categorize test points
#         categories = {
#             'power_nets': [],
#             'signal_nets': [],
#             'ground_nets': [],
#             'clock_nets': [],
#             'differential_pairs': []
#         }
        
#         for point in self.consolidated_points:
#             net_name = point.net_name.upper()
#             if any(keyword in net_name for keyword in ['VCC', 'VDD', 'POWER', '+', 'V3V3', 'V5V0']):
#                 categories['power_nets'].append(point)
#             elif any(keyword in net_name for keyword in ['GND', 'GROUND', 'VSS']):
#                 categories['ground_nets'].append(point)
#             elif any(keyword in net_name for keyword in ['CLK', 'CLOCK', 'OSC']):
#                 categories['clock_nets'].append(point)
#             elif '_P' in net_name or '_N' in net_name:
#                 categories['differential_pairs'].append(point)
#             else:
#                 categories['signal_nets'].append(point)
        
#         # Generate test sequence recommendations
#         test_sequence = []
#         test_sequence.extend(categories['power_nets'])  # Test power first
#         test_sequence.extend(categories['ground_nets'])  # Then ground
#         test_sequence.extend(categories['clock_nets'])   # Then clocks
#         test_sequence.extend(categories['signal_nets'])  # Finally signals
        
#         # Assign priorities
#         for i, point in enumerate(test_sequence):
#             point.test_sequence_priority = i + 1
        
#         report = {
#             'total_test_points': len(self.consolidated_points),
#             'categories': {k: len(v) for k, v in categories.items()},
#             'test_sequence': test_sequence,
#             'fixture_complexity': self.assess_fixture_complexity(),
#             'estimated_cost': self.estimate_fixture_cost(),
#             'manufacturing_time': self.estimate_manufacturing_time(),
#             'density_analysis': self.analyze_fixture_density()
#         }
        
#         return report
    
#     def assess_fixture_complexity(self) -> str:
#         """Assess fixture design complexity"""
#         complexity_factors = 0
        
#         # Check for dual-sided testing
#         if any(p.accessibility == 'Both' for p in self.consolidated_points):
#             complexity_factors += 2
        
#         # Check point density
#         density_analysis = self.analyze_fixture_density()
#         if density_analysis.get('density_status') == 'high':
#             complexity_factors += 2
        
#         # Check for special probe requirements
#         special_probes = sum(1 for p in self.consolidated_points 
#                            if p.probe_recommendations.get('special_requirements'))
#         complexity_factors += min(special_probes // 10, 2)
        
#         if complexity_factors <= 2:
#             return 'Simple'
#         elif complexity_factors <= 4:
#             return 'Moderate' 
#         else:
#             return 'Complex'
    
#     def estimate_fixture_cost(self) -> Dict[str, float]:
#         """Estimate fixture manufacturing cost"""
#         base_cost = 2000  # Base fixture cost in USD
        
#         # Cost per test point
#         point_cost = len(self.consolidated_points) * 15
        
#         # Complexity multiplier
#         complexity = self.assess_fixture_complexity()
#         complexity_multiplier = {'Simple': 1.0, 'Moderate': 1.5, 'Complex': 2.0}.get(complexity, 1.0)
        
#         # Special requirements cost
#         special_cost = 0
#         for point in self.consolidated_points:
#             if point.probe_recommendations.get('special_requirements'):
#                 special_cost += 50
        
#         total_cost = (base_cost + point_cost + special_cost) * complexity_multiplier
        
#         return {
#             'base_cost': base_cost,
#             'point_cost': point_cost,
#             'special_cost': special_cost,
#             'complexity_multiplier': complexity_multiplier,
#             'total_estimated_cost': total_cost
#         }
    
#     def estimate_manufacturing_time(self) -> Dict[str, int]:
#         """Estimate fixture manufacturing time in days"""
#         base_time = 5  # Base manufacturing time
        
#         complexity = self.assess_fixture_complexity()
#         complexity_time = {'Simple': 2, 'Moderate': 5, 'Complex': 10}.get(complexity, 5)
        
#         point_time = max(1, len(self.consolidated_points) // 100)  # 1 day per 100 points
        
#         return {
#             'design_time': base_time + complexity_time,
#             'manufacturing_time': point_time + 3,
#             'testing_time': 2,
#             'total_time': base_time + complexity_time + point_time + 3 + 2
#         }
    
#     def create_test_point_visualization(self) -> go.Figure:
#         """Create interactive visualization of test points"""
#         if not self.consolidated_points:
#             return go.Figure()
        
#         # Prepare data for plotting
#         x_coords = [p.x for p in self.consolidated_points]
#         y_coords = [p.y for p in self.consolidated_points]
#         colors = []
#         sizes = []
#         hover_text = []
        
#         for point in self.consolidated_points:
#             # Color coding by accessibility
#             if point.accessibility == 'Both':
#                 colors.append('green')
#             elif point.accessibility in ['Top', 'Bottom']:
#                 colors.append('blue')
#             else:
#                 colors.append('red')
            
#             # Size by probe diameter
#             probe_diameter = point.probe_recommendations.get('probe_diameter', 1.0)
#             sizes.append(max(8, probe_diameter * 10))
            
#             # Hover information
#             hover_info = (
#                 f"<b>{point.test_point_designation}</b><br>"
#                 f"Net: {point.net_name}<br>"
#                 f"Position: ({point.x:.3f}, {point.y:.3f})<br>"
#                 f"Accessibility: {point.accessibility}<br>"
#                 f"Status: {point.validation_status}<br>"
#                 f"Probe Ø: {probe_diameter:.2f}mm" if probe_diameter else "Probe: TBD"
#             )
#             hover_text.append(hover_info)
        
#         # Create scatter plot
#         fig = go.Figure()
        
#         fig.add_trace(go.Scatter(
#             x=x_coords,
#             y=y_coords,
#             mode='markers',
#             marker=dict(
#                 color=colors,
#                 size=sizes,
#                 opacity=0.7,
#                 line=dict(width=1, color='black')
#             ),
#             text=hover_text,
#             hovertemplate='%{text}<extra></extra>',
#             name='Test Points'
#         ))
        
#         # Add board outline if available
#         if self.board_outline:
#             outline_x = [p[0] for p in self.board_outline] + [self.board_outline[0][0]]
#             outline_y = [p[1] for p in self.board_outline] + [self.board_outline[0][1]]
            
#             fig.add_trace(go.Scatter(
#                 x=outline_x,
#                 y=outline_y,
#                 mode='lines',
#                 line=dict(color='black', width=2),
#                 name='Board Outline',
#                 hoverinfo='skip'
#             ))
        
#         fig.update_layout(
#             title='Test Point Layout Visualization',
#             xaxis_title='X Coordinate (mm)',
#             yaxis_title='Y Coordinate (mm)',
#             showlegend=True,
#             hovermode='closest',
#             width=800,
#             height=600
#         )
        
#         fig.update_xaxis(scaleanchor="y", scaleratio=1)
        
#         return fig
    
#     def create_density_heatmap(self) -> go.Figure:
#         """Create density heatmap of test points"""
#         if not self.consolidated_points:
#             return go.Figure()
        
#         # Create grid for density calculation
#         x_coords = [p.x for p in self.consolidated_points]
#         y_coords = [p.y for p in self.consolidated_points]
        
#         x_min, x_max = min(x_coords), max(x_coords)
#         y_min, y_max = min(y_coords), max(y_coords)
        
#         # Create density grid
#         grid_size = 50
#         x_grid = np.linspace(x_min, x_max, grid_size)
#         y_grid = np.linspace(y_min, y_max, grid_size)
        
#         density_grid = np.zeros((grid_size, grid_size))
        
#         for i, x in enumerate(x_grid):
#             for j, y in enumerate(y_grid):
#                 # Count points within radius
#                 radius = 5.0  # mm
#                 count = sum(1 for p in self.consolidated_points 
#                            if math.sqrt((p.x - x)**2 + (p.y - y)**2) <= radius)
#                 density_grid[j, i] = count
        
#         fig = go.Figure(data=go.Heatmap(
#             z=density_grid,
#             x=x_grid,
#             y=y_grid,
#             colorscale='Viridis',
#             showscale=True,
#             colorbar=dict(title="Points per 5mm radius")
#         ))
        
#         fig.update_layout(
#             title='Test Point Density Heatmap',
#             xaxis_title='X Coordinate (mm)',
#             yaxis_title='Y Coordinate (mm)',
#             width=800,
#             height=600
#         )
        
#         return fig

# # Enhanced Streamlit interface with improved visualizations
# def main():
#     st.set_page_config(
#         page_title="Enhanced CAD Test Point Extractor",
#         page_icon="🔧",
#         layout="wide"
#     )
    
#     st.title("🔧 Enhanced CAD Test Point Extractor")
#     st.markdown("Advanced analysis for bed-of-nails test fixture design with AI-powered insights")
    
#     if not GERBONARA_AVAILABLE:
#         st.stop()
    
#     # Initialize components
#     if 'ollama_client' not in st.session_state:
#         st.session_state.ollama_client = OllamaClient()
    
#     if 'processor' not in st.session_state:
#         st.session_state.processor = EnhancedCADFileProcessor()
    
#     processor = st.session_state.processor
#     ollama_client = st.session_state.ollama_client
    
#     # Enhanced sidebar with fixture parameters
#     with st.sidebar:
#         st.header("Configuration")
        
#         # Model selection
#         available_models = ollama_client.get_available_models()
#         if available_models:
#             selected_model = st.selectbox(
#                 "Select AI Model",
#                 options=available_models,
#                 index=0 if "llama2" in available_models else 0,
#                 help="Choose the AI model for analysis"
#             )
#         else:
#             st.error("❌ Cannot connect to Ollama server")
#             selected_model = None
        
#         st.subheader("Analysis Parameters")
#         tolerance = st.number_input(
#             "Coordinate Tolerance (mm)",
#             min_value=0.001,
#             max_value=1.0,
#             value=0.01,
#             step=0.001,
#             format="%.3f"
#         )
#         processor.coordinate_tolerance = tolerance
        
#         st.subheader("Fixture Parameters")
#         processor.fixture_params['min_probe_spacing'] = st.number_input(
#             "Min Probe Spacing (mm)",
#             min_value=0.5,
#             max_value=5.0,
#             value=1.27,
#             step=0.01
#         )
        
#         processor.fixture_params['max_probe_density'] = st.number_input(
#             "Max Probe Density (probes/mm²)",
#             min_value=0.1,
#             max_value=2.0,
#             value=0.8,
#             step=0.1
#         )
        
#         processor.board_thickness = st.number_input(
#             "Board Thickness (mm)",
#             min_value=0.4,
#             max_value=6.0,
#             value=1.6,
#             step=0.1
#         )
    
#     # File upload section (keeping existing implementation)
#     uploaded_files = st.file_uploader(
#         "Upload CAD Files",
#         accept_multiple_files=True,
#         type=["ASB", "AST", "CPT", "CSP", "FAB", "ipc", "SKC", "SKS",
#               "SMC", "SMS", "SPT", "SSP", "drl", "art", "txt"],
#         help="Upload your Cadence CAD files for analysis"
#     )
    
#     if uploaded_files:
#         # Process files (using existing logic)
#         processor.clear_data()
        
#         # ... (keep existing file processing logic) ...
        
#         # Enhanced analysis after processing
#         if processor.test_points:
#             # Consolidate test points with enhanced analysis
#             if processor.consolidate_test_points():
#                 # Calculate enhanced recommendations for each point
#                 for point in processor.consolidated_points:
#                     point.probe_recommendations = processor.calculate_probe_recommendations(point)
#                     point.keepout_zone = processor.calculate_keepout_zones(point)
                
#                 # Generate fixture report
#                 fixture_report = processor.generate_fixture_report()
                
#                 # Display enhanced results
#                 st.header("Enhanced Test Point Analysis")
                
#                 # Key metrics
#                 col1, col2, col3, col4 = st.columns(4)
#                 with col1:
#                     st.metric("Total Points", fixture_report.get('total_test_points', 0))
#                 with col2:
#                     st.metric("Fixture Complexity", fixture_report.get('fixture_complexity', 'Unknown'))
#                 with col3:
#                     cost_info = fixture_report.get('estimated_cost', {})
#                     st.metric("Est. Cost (USD)", f"${cost_info.get('total_estimated_cost', 0):,.0f}")
#                 with col4:
#                     time_info = fixture_report.get('manufacturing_time', {})
#                     st.metric("Lead Time (days)", time_info.get('total_time', 0))
                
#                 # Visualizations
#                 st.subheader("Test Point Visualizations")
                
#                 col1, col2 = st.columns(2)
                
#                 with col1:
#                     st.plotly_chart(
#                         processor.create_test_point_visualization(),
#                         use_container_width=True
#                     )
                
#                 with col2:
#                     st.plotly_chart(
#                         processor.create_density_heatmap(),
#                         use_container_width=True
#                     )
                
#                 # Detailed fixture report
#                 st.subheader("Fixture Design Report")
                
#                 # Network categories
#                 categories = fixture_report.get('categories', {})
#                 if categories:
#                     st.write("**Signal Categories:**")
#                     category_df = pd.DataFrame([
#                         {"Category": k.replace('_', ' ').title(), "Count": v}
#                         for k, v in categories.items()
#                     ])
#                     st.dataframe(category_df, use_container_width=True)
                
#                 # Density analysis
#                 density_analysis = fixture_report.get('density_analysis', {})
#                 if density_analysis:
#                     st.write("**Density Analysis:**")
#                     col1, col2, col3 = st.columns(3)
#                     with col1:
#                         st.metric("Point Density", f"{density_analysis.get('point_density', 0):.2f} pts/mm²")
#                     with col2:
#                         st.metric("Board Area", f"{density_analysis.get('board_area_mm2', 0):.1f} mm²")
#                     with col3:
#                         status = density_analysis.get('density_status', 'unknown')
#                         st.metric("Density Status", status.title())
                    
#                     if density_analysis.get('fixture_recommendations'):
#                         st.write("**Recommendations:**")
#                         for rec in density_analysis['fixture_recommendations']:
#                             st.write(f"• {rec}")
                
#                 # Cost breakdown
#                 cost_info = fixture_report.get('estimated_cost', {})
#                 if cost_info:
#                     st.subheader("Cost Breakdown")
#                     cost_df = pd.DataFrame([
#                         {"Component", "Cost (USD)"},
#                         ["Base Fixture", f"${cost_info.get('base_cost', 0):,.0f}"],
#                         ["Test Points", f"${cost_info.get('point_cost', 0):,.0f}"],
#                         ["Special Requirements", f"${cost_info.get('special_cost', 0):,.0f}"],
#                         ["Complexity Factor", f"{cost_info.get('complexity_multiplier', 1):.1f}x"],
#                         ["**Total Estimated**", f"**${cost_info.get('total_estimated_cost', 0):,.0f}**"]
#                     ])
#                     st.table(cost_df)
                
#                 # Enhanced AI analysis
#                 if selected_model and processor.consolidated_points:
#                     st.header("AI-Powered Fixture Analysis")
                    
#                     # Prepare enhanced data for AI analysis
#                     enhanced_data = {
#                         'total': len(processor.consolidated_points),
#                         'valid': len([p for p in processor.consolidated_points if p.validation_status == "Valid"]),
#                         'top_accessible': len([p for p in processor.consolidated_points if "Top" in p.accessibility]),
#                         'bottom_accessible': len([p for p in processor.consolidated_points if "Bottom" in p.accessibility]),
#                         'complexity': fixture_report.get('fixture_complexity', 'Unknown'),
#                         'estimated_cost': cost_info.get('total_estimated_cost', 0),
#                         'density_status': density_analysis.get('density_status', 'unknown'),
#                         'special_requirements': sum(1 for p in processor.consolidated_points 
#                                                   if p.probe_recommendations.get('special_requirements'))
#                     }
                    
#                     with st.spinner(f"Generating enhanced analysis using {selected_model}..."):
#                         analysis = ollama_client.analyze_test_points(enhanced_data, selected_model)
                        
#                         if analysis:
#                             st.markdown(analysis)
#                         else:
#                             st.error("Failed to generate AI analysis")
    
#     else:
#         st.info("Please upload CAD files to begin enhanced analysis")

# if __name__ == "__main__":
#     main()