from typing import List

import dash_daq as daq
import dash_html_components as html
from constant_sorrow.constants import UNKNOWN_FLEET_STATE
from maya import MayaDT
from pendulum.parsing import ParserError

import nucypher

NODE_TABLE_COLUMNS = ['Status', 'Checksum', 'Nickname', 'Launched', 'Last Seen', 'Fleet State']


def header() -> html.Div:
    return html.Div([html.Div(f'v{nucypher.__version__}', id='version')], className="logo-widget")


def state_detail(state: dict, current_state: bool) -> html.Div:
    children = [
        html.Div([
            html.Div(state['symbol'], className='single-symbol'),
        ], className='nucypher-nickname-icon', style={'border-color': state['color_hex']}),
        html.Span(state['nickname'], title=state['updated'])]

    if current_state:
        # add current annotation to children
        children.append(html.Span('(*Current)'))

    detail = html.Div(children=children,
                      className='state state-current' if current_state else 'state',
                      style={'background-color': state['color_hex']})
    return detail


def _states_table(states: List[dict]) -> html.Table:
    row = []
    for idx, state_dict in enumerate(states):
        # add previous states in order (already reversed)
        current_state = (idx == 0)
        row.append(html.Td(state_detail(state=state_dict, current_state=current_state)))
    return html.Table([html.Tr(row, id='state-table')])


def previous_states(states: List[dict]) -> html.Div:
    return html.Div([
        html.H4('Previous States'),
        html.Div([
            _states_table(states)
        ]),
    ], className='row')


def generate_node_status_icon(status: dict) -> html.Td:
    # TODO: daq loading issue with dash >1.5.0
    # https://community.plot.ly/t/solved-intermittent-dash-dependency-exception-dash-daq-is-registered-but-the-path-requested-is-not-valid/31563
    status_message, color = status['status'], status['color']
    status_cell = daq.Indicator(id='Status',
                                color=color,
                                value=True,
                                label=status_message,
                                labelPosition='right',
                                size=25)  # pixels
    status = html.Td(status_cell)
    return status


def generate_node_table_components(node_info: dict) -> dict:

    identity = html.Td(children=html.Div([
        html.A(node_info['nickname'],
               href=f'https://{node_info["rest_url"]}/status',
               target='_blank')
    ]))

    # Fleet State
    fleet_state_div = []
    fleet_state_icon = node_info['fleet_state_icon']
    if fleet_state_icon is not UNKNOWN_FLEET_STATE:
        icon_list = node_info['fleet_state_icon']
        fleet_state_div = icon_list
    fleet_state = html.Td([html.Div(fleet_state_div)])

    staker_address = node_info['staker_address']
    etherscan_url = f'https://goerli.etherscan.io/address/{node_info["staker_address"]}'
    try:
        slang_last_seen = MayaDT.from_rfc3339(node_info['last_seen']).slang_time()
    except ParserError:
        slang_last_seen = node_info['last_seen']

    status = generate_node_status_icon(node_info['status'])
    components = {
        'Status': status,
        'Checksum': html.Td(html.A(f'{staker_address[:10]}...', href=etherscan_url, target='_blank')),
        'Nickname': identity,
        'Launched': html.Td(node_info['timestamp']),
        'Last Seen': html.Td([slang_last_seen]),
        'Fleet State': fleet_state
    }

    return components


def nodes_table(nodes, teacher_index: int) -> html.Table:
    rows = []
    for index, node_info in enumerate(nodes):
        row = []
        # TODO: could return list (skip column for-loop); however, dict is good in case of re-ordering of columns
        components = generate_node_table_components(node_info=node_info)

        for col in NODE_TABLE_COLUMNS:
            cell = components[col]
            if cell:
                row.append(cell)

        style_dict = {'overflowY': 'scroll'}
        # highlight teacher
        if index == teacher_index:
            style_dict['backgroundColor'] = '#1E65F3'
            style_dict['color'] = 'white'

        rows.append(html.Tr(row, style=style_dict, className='node-row'))

    table = html.Table(
        # header
        [html.Tr([html.Th(col) for col in NODE_TABLE_COLUMNS], className='table-header')] +
        rows,
        id='node-table'
    )

    return table


def known_nodes(nodes_dict: dict, teacher_checksum: str = None) -> html.Div:
    nodes = list()
    teacher_index = None
    for checksum in nodes_dict:
        node_data = nodes_dict[checksum]
        if node_data:
            if checksum == teacher_checksum:
                teacher_index = len(nodes)
            nodes.append(node_data)

    component = html.Div([
        html.H4('Network Nodes'),
        html.Div([
            html.Div('* Current Teacher',
                     style={'backgroundColor': '#1E65F3', 'color': 'white'},
                     className='two columns'),
        ]),
        html.Br(),
        html.H6(f'Known Nodes: {len(nodes_dict)}'),
        html.Div([nodes_table(nodes, teacher_index)])
    ])
    return component
