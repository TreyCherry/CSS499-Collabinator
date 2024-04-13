# alerts.py
from datagate import DataGate

# Assuming STATES from another module
from your_constants_module import STATES

def update_document_state(document_id, new_state):
    # Update doc state
    datagate = DataGate()
    current_state = datagate.get_document_state(document_id)

    if current_state != new_state:
        datagate.update_document_state(document_id, new_state)
        generate_alert(document_id, new_state)

def generate_alert(document_id, new_state):
    # Generate/store alert
    datagate = DataGate()
    alert_message = f"Document {document_id} state changed to {STATES[new_state].name}"
    recipient_id = datagate.get_document_owner(document_id)
    datagate.addAlert(recipient_id, alert_message)

# DataGate extensions
def DataGate_get_document_state(self, document_id):
    # Fetch doc state
    query = "SELECT document_stage FROM Document WHERE document_id=?"
    result = self.execute_query(query, (document_id,))
    return result.fetchone()[0]

def DataGate_update_document_state(self, document_id, new_state):
    # Update doc state in DB
    query = "UPDATE Document SET document_stage=? WHERE document_id=?"
    self.execute_query(query, (new_state, document_id))
    self.connection.commit()

def DataGate_get_document_owner(self, document_id):
    # Fetch doc owner
    query = "SELECT assigned_employee FROM Document WHERE document_id=?"
    result = self.execute_query(query, (document_id,))
    return result.fetchone()[0]

# Attach methods to DataGate
setattr(DataGate, "get_document_state", DataGate_get_document_state)
setattr(DataGate, "update_document_state", DataGate_update_document_state)
setattr(DataGate, "get_document_owner", DataGate_get_document_owner)

