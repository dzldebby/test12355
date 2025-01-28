import React, { useState } from 'react';
import { Container, Row, Col, Form, Button, Spinner, Table, Accordion } from 'react-bootstrap';
import { formatNumber } from './utils';
import { calculateBankInterest, optimizeBankDistribution } from './calculations';

function App() {
  // State management
  const [investmentAmount, setInvestmentAmount] = useState('10,000');
  const [hasSalary, setHasSalary] = useState(false);
  const [salaryAmount, setSalaryAmount] = useState(5000);
  const [cardSpend, setCardSpend] = useState(500);
  const [isCalculating, setIsCalculating] = useState(false);
  const [comparisonResults, setComparisonResults] = useState(null);
  const [optimizationResults, setOptimizationResults] = useState(null);

  // Handle investment amount input with comma formatting
  const handleAmountChange = (e) => {
    const value = e.target.value.replace(/[^\d,]/g, '');
    setInvestmentAmount(value);
  };

  // Generate comparison table
  const handleGenerateComparison = async () => {
    setIsCalculating(true);
    try {
      const amount = parseInt(investmentAmount.replace(/,/g, ''));
      const baseRequirements = {
        hasSalary: hasSalary && salaryAmount >= 3000,
        meetsCriteriaA: cardSpend >= 500,
      };

      const bankResults = [];
      const banks = ["UOB One", "SC BonusSaver", "OCBC 360", "BOC SmartSaver", "Chocolate"];
      
      for (const bank of banks) {
        const bankReqs = { ...baseRequirements };
        if (bank === "UOB One") {
          bankReqs.hasSalary = false;
        }
        const results = await calculateBankInterest(amount, bank, bankReqs);
        bankResults.push({
          bank,
          monthlyInterest: results.totalInterest / 12,
          annualInterest: results.totalInterest,
          breakdown: results.breakdown,
        });
      }
      
      setComparisonResults(bankResults);
    } catch (error) {
      console.error(error);
      alert('An error occurred while calculating interest rates.');
    }
    setIsCalculating(false);
  };

  // Generate optimal distribution
  const handleGenerateOptimal = async () => {
    setIsCalculating(true);
    try {
      const amount = parseInt(investmentAmount.replace(/,/g, ''));
      const baseRequirements = {
        hasSalary: hasSalary && salaryAmount >= 3000,
        meetsCriteriaA: cardSpend >= 500,
      };

      const results = await optimizeBankDistribution(amount, baseRequirements);
      setOptimizationResults(results);
    } catch (error) {
      console.error(error);
      alert('An error occurred while calculating optimal distribution.');
    }
    setIsCalculating(false);
  };

  return (
    <Container className="py-4">
      <h1>Bank Interest Rate Optimizer</h1>

      {/* Input Section */}
      <Form className="my-4">
        <Form.Group className="mb-3">
          <Form.Label>Investment Amount ($)</Form.Label>
          <Form.Control
            type="text"
            value={investmentAmount}
            onChange={handleAmountChange}
            placeholder="Enter amount (e.g., 100,000)"
          />
        </Form.Group>

        <h2 className="h4 mt-4">Your Banking Activities</h2>
        
        <Accordion className="mb-3">
          <Accordion.Item eventKey="0">
            <Accordion.Header>Salary Credit</Accordion.Header>
            <Accordion.Body>
              <Form.Check
                type="checkbox"
                label="Credit salary via GIRO"
                checked={hasSalary}
                onChange={(e) => setHasSalary(e.target.checked)}
              />
              {hasSalary && (
                <Form.Group className="mt-3">
                  <Form.Label>Monthly Salary Amount ($)</Form.Label>
                  <Form.Range
                    min={0}
                    max={50000}
                    step={100}
                    value={salaryAmount}
                    onChange={(e) => setSalaryAmount(parseInt(e.target.value))}
                  />
                  <div>Selected: ${formatNumber(salaryAmount)}</div>
                </Form.Group>
              )}
            </Accordion.Body>
          </Accordion.Item>

          <Accordion.Item eventKey="1">
            <Accordion.Header>Credit Card Spending</Accordion.Header>
            <Accordion.Body>
              <Form.Group>
                <Form.Label>Monthly Card Spend ($)</Form.Label>
                <Form.Range
                  min={0}
                  max={10000}
                  step={100}
                  value={cardSpend}
                  onChange={(e) => setCardSpend(parseInt(e.target.value))}
                />
                <div>Selected: ${formatNumber(cardSpend)}</div>
              </Form.Group>
            </Accordion.Body>
          </Accordion.Item>
        </Accordion>
      </Form>

      {/* Action Buttons */}
      <Row className="g-3 mb-4">
        <Col xs={12} md={6}>
          <Button 
            variant="secondary" 
            className="w-100"
            onClick={handleGenerateComparison}
            disabled={isCalculating}
          >
            {isCalculating ? (
              <><Spinner size="sm" /> Calculating...</>
            ) : (
              'Generate Interest Rates Comparison'
            )}
          </Button>
        </Col>
        <Col xs={12} md={6}>
          <Button 
            variant="primary" 
            className="w-100"
            onClick={handleGenerateOptimal}
            disabled={isCalculating}
          >
            {isCalculating ? (
              <><Spinner size="sm" /> Calculating...</>
            ) : (
              'Generate Optimal Distribution'
            )}
          </Button>
        </Col>
      </Row>

      {/* Results Section */}
      {comparisonResults && (
        <section className="mb-4">
          <h2>Interest Rates Comparison</h2>
          <Table responsive striped bordered>
            <thead>
              <tr>
                <th>Bank</th>
                <th>Monthly Interest</th>
                <th>Annual Interest</th>
              </tr>
            </thead>
            <tbody>
              {comparisonResults.map((result) => (
                <tr key={result.bank}>
                  <td>{result.bank}</td>
                  <td>${formatNumber(result.monthlyInterest)}</td>
                  <td>${formatNumber(result.annualInterest)}</td>
                </tr>
              ))}
            </tbody>
          </Table>
          
          <Accordion>
            {comparisonResults.map((result) => (
              <Accordion.Item key={result.bank} eventKey={result.bank}>
                <Accordion.Header>{result.bank} Breakdown</Accordion.Header>
                <Accordion.Body>
                  {/* Render breakdown details */}
                </Accordion.Body>
              </Accordion.Item>
            ))}
          </Accordion>
        </section>
      )}

      {optimizationResults && (
        <section>
          <h2>Optimal Distribution Results</h2>
          {optimizationResults.map((solution, index) => (
            <div key={index} className="mb-4">
              <h3>Scenario {index + 1}</h3>
              {/* Render optimization results */}
            </div>
          ))}
        </section>
      )}
    </Container>
  );
}

export default App;